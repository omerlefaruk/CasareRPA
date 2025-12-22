import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const url = new URL(req.url)
  const pathParts = url.pathname.split('/')
  const tenantSlug = pathParts[pathParts.length - 1]

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  )

  if (req.method === 'GET') {
    const mode = url.searchParams.get('hub.mode')
    const token = url.searchParams.get('hub.verify_token')
    const challenge = url.searchParams.get('hub.challenge')

    if (mode === 'subscribe' && token) {
      const { data: appConfig } = await supabase
        .from('tenant_whatsapp_apps')
        .select('verify_token')
        .eq('tenant_id', (await getTenantId(supabase, tenantSlug)))
        .single()

      if (appConfig && appConfig.verify_token === token) {
        return new Response(challenge, { status: 200 })
      }
    }
    return new Response('Forbidden', { status: 403 })
  }

  if (req.method === 'POST') {
    const payload = await req.json()

    // TODO: verify the subscriber signature (X-Hub-Signature-256) using the tenant app secret
    const n8nUrl = Deno.env.get('N8N_WEBHOOK_URL')
    fetch(n8nUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-tenant-slug': tenantSlug },
      body: JSON.stringify(payload)
    })

    return new Response('OK', { status: 200 })
  }

  return new Response('Method not allowed', { status: 405 })
})

async function getTenantId(supabase, slug) {
  const { data } = await supabase.from('tenants').select('id').eq('slug', slug).single()
  return data?.id
}
