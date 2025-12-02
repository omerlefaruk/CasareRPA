// CasareRPA Job Notification Edge Function
// Sends webhook notifications when job status changes.
//
// Deploy: supabase functions deploy job-notification
// Trigger: Set up as Database Webhook on jobs table in Supabase Dashboard
//
// Database Webhook Setup:
// 1. Go to Database > Webhooks
// 2. Create webhook on 'jobs' table
// 3. Events: UPDATE (filter: status column changed)
// 4. URL: https://<project-ref>.supabase.co/functions/v1/job-notification

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

interface JobRecord {
  job_id: string;
  workflow_id: string;
  workflow_name?: string;
  status: string;
  robot_id?: string;
  robot_uuid?: string;
  progress?: number;
  current_node?: string;
  duration_ms?: number;
  error?: string;
  result?: Record<string, unknown>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

interface WebhookPayload {
  type: "UPDATE" | "INSERT" | "DELETE";
  table: string;
  schema: string;
  record: JobRecord;
  old_record?: JobRecord;
}

interface NotificationPayload {
  event: string;
  timestamp: string;
  job: {
    id: string;
    workflow_id: string;
    workflow_name: string;
    status: string;
    robot_id?: string;
    progress?: number;
    duration_ms?: number;
    error?: string;
  };
  previous_status?: string;
}

// Status transitions that trigger notifications
const NOTIFICATION_EVENTS: Record<string, string> = {
  pending: "job.created",
  running: "job.started",
  completed: "job.completed",
  failed: "job.failed",
  cancelled: "job.cancelled",
  timeout: "job.timeout",
};

Deno.serve(async (req: Request): Promise<Response> => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Parse webhook payload
    const payload: WebhookPayload = await req.json();

    // Only process job status changes
    if (payload.table !== "jobs" || payload.type !== "UPDATE") {
      return new Response(
        JSON.stringify({ message: "Ignored: not a job update" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const record = payload.record;
    const oldRecord = payload.old_record;

    // Check if status actually changed
    if (oldRecord && record.status === oldRecord.status) {
      return new Response(
        JSON.stringify({ message: "Ignored: status unchanged" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Determine event type
    const eventType = NOTIFICATION_EVENTS[record.status];
    if (!eventType) {
      return new Response(
        JSON.stringify({
          message: `Ignored: status '${record.status}' not configured for notifications`,
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Check if this event type should be notified
    const enabledEvents = (
      Deno.env.get("NOTIFICATION_EVENTS") || "job.completed,job.failed"
    ).split(",");
    if (!enabledEvents.includes(eventType)) {
      return new Response(
        JSON.stringify({ message: `Ignored: event '${eventType}' not enabled` }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Get webhook URL
    const webhookUrl = Deno.env.get("JOB_NOTIFICATION_WEBHOOK");
    if (!webhookUrl) {
      console.log("No webhook URL configured, skipping notification");
      return new Response(
        JSON.stringify({ message: "No webhook URL configured" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Build notification payload
    const notification: NotificationPayload = {
      event: eventType,
      timestamp: new Date().toISOString(),
      job: {
        id: record.job_id,
        workflow_id: record.workflow_id,
        workflow_name: record.workflow_name || "Unknown",
        status: record.status,
        robot_id: record.robot_id || record.robot_uuid,
        progress: record.progress,
        duration_ms: record.duration_ms,
        error: record.error,
      },
      previous_status: oldRecord?.status,
    };

    // Send notification to webhook
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "CasareRPA-Notifier/1.0",
        "X-CasareRPA-Event": eventType,
      },
      body: JSON.stringify(notification),
    });

    if (!response.ok) {
      console.error(
        `Webhook failed: ${response.status} ${response.statusText}`
      );
      // Log failure but don't throw - webhook failures shouldn't block job processing
      await logNotificationFailure(record.job_id, eventType, response.status);
    }

    // Optionally log to Supabase for audit
    await logNotificationSent(record.job_id, eventType, response.ok);

    return new Response(
      JSON.stringify({
        success: response.ok,
        event: eventType,
        job_id: record.job_id,
        webhook_status: response.status,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    console.error("Notification error:", errorMessage);

    return new Response(
      JSON.stringify({
        success: false,
        error: errorMessage,
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});

// Helper function to log successful notifications
async function logNotificationSent(
  jobId: string,
  eventType: string,
  success: boolean
): Promise<void> {
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    if (!supabaseUrl || !supabaseServiceKey) return;

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: { autoRefreshToken: false, persistSession: false },
    });

    // Update job metadata with notification info
    await supabase
      .from("jobs")
      .update({
        metadata: {
          last_notification: {
            event: eventType,
            timestamp: new Date().toISOString(),
            success: success,
          },
        },
      })
      .eq("job_id", jobId);
  } catch (e) {
    console.error("Failed to log notification:", e);
  }
}

// Helper function to log notification failures
async function logNotificationFailure(
  jobId: string,
  eventType: string,
  statusCode: number
): Promise<void> {
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    if (!supabaseUrl || !supabaseServiceKey) return;

    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: { autoRefreshToken: false, persistSession: false },
    });

    // Log failure to robot_logs for visibility
    await supabase.from("robot_logs").insert({
      robot_id: "00000000-0000-0000-0000-000000000000", // System robot ID
      tenant_id: "00000000-0000-0000-0000-000000000000",
      timestamp: new Date().toISOString(),
      level: "WARNING",
      message: `Webhook notification failed for job ${jobId}`,
      source: "job-notification-function",
      extra: {
        job_id: jobId,
        event: eventType,
        webhook_status: statusCode,
      },
    });
  } catch (e) {
    console.error("Failed to log notification failure:", e);
  }
}
