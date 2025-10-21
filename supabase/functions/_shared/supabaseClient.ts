// @ts-ignore - remote module resolved by Deno at runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Declare Deno global for TypeScript tooling in this repo
declare global {
  const Deno: {
    env: {
      get: (key: string) => string | undefined;
    };
    serve: (handler: (request: Request) => Response | Promise<Response>) => void;
  };
}

const supabaseUrl = Deno.env.get("SUPABASE_URL");
const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

if (!supabaseUrl) {
  throw new Error("Missing SUPABASE_URL environment variable");
}

if (!serviceRoleKey) {
  throw new Error("Missing SUPABASE_SERVICE_ROLE_KEY environment variable");
}

export const supabase = createClient(supabaseUrl, serviceRoleKey, {
  auth: {
    persistSession: false,
  },
  global: {
    headers: {
      "X-Client-Info": "ai-tech-news-assistant-edge",
    },
  },
});
