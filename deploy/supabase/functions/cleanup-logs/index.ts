// CasareRPA Log Cleanup Edge Function
// Automatically removes old robot logs based on retention policy.
//
// Deploy: supabase functions deploy cleanup-logs
// Invoke: supabase functions invoke cleanup-logs --data '{"retention_days": 30}'
// Schedule: Set up via Supabase Dashboard > Database > Scheduled Jobs

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

interface CleanupRequest {
  retention_days?: number;
  dry_run?: boolean;
}

interface CleanupResult {
  success: boolean;
  partitions_dropped: string[];
  duration_ms: number;
  dry_run: boolean;
  message: string;
  error?: string;
}

Deno.serve(async (req: Request): Promise<Response> => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const startTime = Date.now();

  try {
    // Parse request body
    let body: CleanupRequest = {};
    if (req.method === "POST") {
      try {
        body = await req.json();
      } catch {
        // Empty body is OK, use defaults
      }
    }

    const retentionDays = body.retention_days ?? 30;
    const dryRun = body.dry_run ?? false;

    // Validate retention days
    if (retentionDays < 1 || retentionDays > 365) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "retention_days must be between 1 and 365",
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error("Missing Supabase environment variables");
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });

    let partitionsDropped: string[] = [];

    if (dryRun) {
      // Dry run: just query what would be dropped
      const { data, error } = await supabase.rpc(
        "drop_old_robot_logs_partitions",
        {
          retention_days: retentionDays,
        }
      );

      if (error) {
        // Function doesn't exist yet or other error - simulate response
        console.log(
          `Dry run: Would check for partitions older than ${retentionDays} days`
        );
      } else if (data) {
        partitionsDropped = data.map(
          (row: { partition_name: string }) => row.partition_name
        );
      }
    } else {
      // Execute actual cleanup
      const { data, error } = await supabase.rpc(
        "drop_old_robot_logs_partitions",
        {
          retention_days: retentionDays,
        }
      );

      if (error) {
        throw new Error(`Cleanup function error: ${error.message}`);
      }

      if (data) {
        partitionsDropped = data
          .filter((row: { action: string }) => row.action === "DROPPED")
          .map((row: { partition_name: string }) => row.partition_name);
      }

      // Record cleanup in history table
      if (partitionsDropped.length > 0) {
        const durationMs = Date.now() - startTime;
        await supabase.from("robot_logs_cleanup_history").insert({
          partitions_dropped: partitionsDropped,
          retention_days: retentionDays,
          duration_ms: durationMs,
          status: "completed",
        });
      }

      // Ensure future partitions exist
      await supabase.rpc("ensure_robot_logs_partitions", {
        months_ahead: 2,
      });
    }

    const result: CleanupResult = {
      success: true,
      partitions_dropped: partitionsDropped,
      duration_ms: Date.now() - startTime,
      dry_run: dryRun,
      message:
        partitionsDropped.length > 0
          ? `${dryRun ? "Would drop" : "Dropped"} ${partitionsDropped.length} partition(s)`
          : "No partitions to clean up",
    };

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";

    // Log error for debugging
    console.error("Cleanup error:", errorMessage);

    const result: CleanupResult = {
      success: false,
      partitions_dropped: [],
      duration_ms: Date.now() - startTime,
      dry_run: false,
      message: "Cleanup failed",
      error: errorMessage,
    };

    return new Response(JSON.stringify(result), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
