import { supabase } from "../_shared/supabaseClient.ts";

interface SemanticSearchRequest {
  query: string;
  topK?: number;
  model?: string;
}

interface OpenAIEmbeddingResponse {
  data?: Array<{
    embedding: number[];
  }>;
}

interface EmbeddingResult {
  article_id: number;
  similarity: number;
  article: {
    id: number;
    title: string;
    summary: string | null;
    content: string | null;
    url: string | null;
    source: string | null;
    published_at: string | null;
    categories: string[] | null;
  };
}

const DEFAULT_MODEL = "text-embedding-3-large";
const DEFAULT_TOP_K = 10;
const MAX_TOP_K = 50;

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};
const openAiApiKey = Deno.env.get("OPENAI_API_KEY");

if (!openAiApiKey) {
  throw new Error("Missing OPENAI_API_KEY environment variable");
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method === "OPTIONS") {
      return new Response("ok", {
        status: 200,
        headers: corsHeaders,
      });
    }

    if (req.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const body = (await req.json()) as SemanticSearchRequest;

    const query = body.query?.trim();

    if (!query) {
      return new Response(JSON.stringify({ error: "Query is required" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const requestedTopK = Number.isInteger(body.topK)
      ? (body.topK as number)
      : DEFAULT_TOP_K;
    const topK = Math.min(Math.max(requestedTopK, 1), MAX_TOP_K);
    const model = body.model ?? DEFAULT_MODEL;

    const embeddingResponse = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${openAiApiKey}`,
      },
      body: JSON.stringify({ input: query, model }),
    });

    if (!embeddingResponse.ok) {
      const errorText = await embeddingResponse.text();
      throw new Error(`Failed to generate embeddings: ${errorText}`);
    }

    const embeddingData = (await embeddingResponse.json()) as OpenAIEmbeddingResponse;
    const embedding = embeddingData.data?.[0]?.embedding ?? [];

    if (!Array.isArray(embedding) || embedding.length === 0) {
      throw new Error("Invalid embedding response from OpenAI");
    }

    const { data, error } = await supabase.rpc<EmbeddingResult>("match_articles", {
      query_embedding: embedding as number[],
      match_count: topK,
    });

    if (error) {
      throw error;
    }

    return new Response(
      JSON.stringify({
        success: true,
        query,
        results: data ?? [],
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Semantic search error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
