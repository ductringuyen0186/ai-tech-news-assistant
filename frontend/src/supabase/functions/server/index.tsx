import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import * as kv from "./kv_store.tsx";
const app = new Hono();

// Enable logger
app.use('*', logger(console.log));

// Enable CORS for all routes and methods
app.use(
  "/*",
  cors({
    origin: "*",
    allowHeaders: ["Content-Type", "Authorization"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    exposeHeaders: ["Content-Length"],
    maxAge: 600,
  }),
);

// Health check endpoint
app.get("/make-server-3889d4d6/health", (c) => {
  return c.json({ status: "ok" });
});

// Mock news data (in production, this would come from RSS feeds, NewsAPI, etc.)
const MOCK_NEWS_DATA = [
  {
    id: "1",
    title: "OpenAI Unveils GPT-5 with Revolutionary Multi-Modal Capabilities",
    source: "TechCrunch",
    url: "https://techcrunch.com",
    publishedAt: "2025-10-17T10:30:00Z",
    imageUrl: "https://images.unsplash.com/photo-1625314887424-9f190599bd56?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhcnRpZmljaWFsJTIwaW50ZWxsaWdlbmNlJTIwcm9ib3R8ZW58MXx8fHwxNzYwNjM1MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["AI/ML", "AI Agents"],
    content: "OpenAI has announced GPT-5, their most advanced language model yet...",
    summaryShort: "OpenAI launches GPT-5 with enhanced reasoning and multi-modal understanding.",
    summaryMedium: "OpenAI today announced GPT-5, featuring breakthrough advances in reasoning, multi-modal understanding, and agentic capabilities. The new model can process video, audio, and images simultaneously while maintaining context across longer conversations. Early benchmarks show 40% improvement over GPT-4 in complex reasoning tasks.",
    keyInsights: ["40% improvement in reasoning tasks", "Native multi-modal processing", "Enhanced context window (500K tokens)", "Built-in tool use and function calling"],
    sentiment: "positive",
    trending: true
  },
  {
    id: "2",
    title: "CRISPR Breakthrough: Gene Editing Cures Rare Blood Disease in Clinical Trial",
    source: "Wired",
    url: "https://wired.com",
    publishedAt: "2025-10-17T09:15:00Z",
    imageUrl: "https://images.unsplash.com/photo-1668600372069-e39ec2ab28af?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiaW90ZWNoJTIwc2NpZW5jZSUyMGxhYm9yYXRvcnl8ZW58MXx8fHwxNzYwNzI4NzIwfDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Biotech", "Healthcare"],
    content: "A major clinical trial demonstrates successful gene editing treatment...",
    summaryShort: "CRISPR therapy shows 95% success rate in treating rare genetic blood disorder.",
    summaryMedium: "Researchers announced breakthrough results from a Phase III clinical trial where CRISPR-based gene editing successfully treated 95% of patients with a rare blood disease. The treatment involves editing specific genes in patient's stem cells, marking a significant milestone in personalized medicine. FDA approval is expected within 6 months.",
    keyInsights: ["95% success rate across 200 patients", "One-time treatment with lasting effects", "FDA fast-track approval pending", "Could be applied to other genetic disorders"],
    sentiment: "positive",
    trending: true
  },
  {
    id: "3",
    title: "U.S. Military Deploys AI-Powered Autonomous Drone Swarms",
    source: "Ars Technica",
    url: "https://arstechnica.com",
    publishedAt: "2025-10-17T08:00:00Z",
    imageUrl: "https://images.unsplash.com/photo-1731579884331-95c1da04e988?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtaWxpdGFyeSUyMHRlY2hub2xvZ3klMjBkcm9uZXxlbnwxfHx8fDE3NjA3Mjg3MjB8MA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Military Tech", "AI/ML"],
    content: "The Department of Defense has successfully tested autonomous drone swarms...",
    summaryShort: "Pentagon demonstrates coordinated AI drone swarms capable of autonomous decision-making.",
    summaryMedium: "The U.S. Department of Defense conducted its largest autonomous drone swarm test, demonstrating 1,000+ drones operating with AI-driven coordination. The swarms can adapt to changing conditions, communicate without central command, and make tactical decisions autonomously. This represents a major shift in military technology and raises important ethical questions.",
    keyInsights: ["1,000+ drones coordinated autonomously", "Distributed AI decision-making", "No single point of failure", "Raises ethical concerns about autonomous weapons"],
    sentiment: "mixed",
    trending: true
  },
  {
    id: "4",
    title: "Apple Silicon M4 Pro Breaks Performance Records, Challenges NVIDIA",
    source: "The Verge",
    url: "https://theverge.com",
    publishedAt: "2025-10-17T07:30:00Z",
    imageUrl: "https://images.unsplash.com/photo-1760199789464-eff5ba507e32?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWNobm9sb2d5JTIwbmV3cyUyMGRpZ2l0YWx8ZW58MXx8fHwxNzYwNzI4NzE5fDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Hardware", "AI/ML"],
    content: "Apple's new M4 Pro chip delivers unprecedented performance...",
    summaryShort: "Apple M4 Pro chip achieves breakthrough AI inference speeds rivaling datacenter GPUs.",
    summaryMedium: "Apple's M4 Pro processor is setting new benchmarks in both CPU and AI performance, with the neural engine delivering speeds comparable to NVIDIA's datacenter GPUs for certain workloads. The chip features 40 CPU cores and 128GB unified memory, making it ideal for AI developers. Industry analysts predict this could accelerate on-device AI adoption.",
    keyInsights: ["Matches NVIDIA GPU performance for inference", "128GB unified memory architecture", "60% more power efficient than competitors", "Could accelerate edge AI deployment"],
    sentiment: "positive",
    trending: false
  },
  {
    id: "5",
    title: "Quantum Computing Startup Achieves 1000-Qubit Milestone",
    source: "MIT Technology Review",
    url: "https://technologyreview.com",
    publishedAt: "2025-10-16T16:00:00Z",
    imageUrl: "https://images.unsplash.com/photo-1760199789464-eff5ba507e32?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWNobm9sb2d5JTIwbmV3cyUyMGRpZ2l0YWx8ZW58MXx8fHwxNzYwNzI4NzE5fDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Quantum Computing", "Hardware"],
    content: "A Silicon Valley startup announced a major breakthrough in quantum computing...",
    summaryShort: "Startup builds 1000-qubit quantum computer with record error correction.",
    summaryMedium: "QuantumCore, a well-funded startup, revealed a 1000-qubit quantum processor with industry-leading error correction rates. The achievement puts them ahead of IBM and Google in the race toward practical quantum advantage. The company plans to offer cloud access to researchers by Q1 2026.",
    keyInsights: ["1000 logical qubits with error correction", "10x better coherence time than competitors", "Cloud access launching Q1 2026", "$500M Series C funding round"],
    sentiment: "positive",
    trending: false
  },
  {
    id: "6",
    title: "Tesla's Optimus Robot Now Commercially Available for $20,000",
    source: "TechCrunch",
    url: "https://techcrunch.com",
    publishedAt: "2025-10-16T14:00:00Z",
    imageUrl: "https://images.unsplash.com/photo-1625314887424-9f190599bd56?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhcnRpZmljaWFsJTIwaW50ZWxsaWdlbmNlJTIwcm9ib3R8ZW58MXx8fHwxNzYwNjM1MTA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Robotics", "AI Agents"],
    content: "Tesla begins shipping Optimus humanoid robots to commercial customers...",
    summaryShort: "Tesla ships first commercial Optimus robots at $20K price point.",
    summaryMedium: "Tesla has begun delivering Optimus humanoid robots to select commercial customers, with broader availability planned for 2026. The $20,000 robot can perform basic warehouse tasks, household chores, and light assembly work. Early reviews highlight impressive dexterity but note limitations in complex problem-solving.",
    keyInsights: ["First commercial humanoid robot under $25K", "Can perform 50+ different tasks", "8-hour battery life", "Limited cognitive capabilities currently"],
    sentiment: "positive",
    trending: false
  },
  {
    id: "7",
    title: "New Security Flaw Found in Popular Cloud Infrastructure",
    source: "Hacker News",
    url: "https://news.ycombinator.com",
    publishedAt: "2025-10-16T12:00:00Z",
    imageUrl: "https://images.unsplash.com/photo-1760199789464-eff5ba507e32?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWNobm9sb2d5JTIwbmV3cyUyMGRpZ2l0YWx8ZW58MXx8fHwxNzYwNzI4NzE5fDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Security", "Cloud"],
    content: "Security researchers discovered critical vulnerability affecting millions...",
    summaryShort: "Critical zero-day vulnerability discovered in AWS, Azure, and GCP services.",
    summaryMedium: "Security researchers have identified a critical zero-day vulnerability affecting major cloud providers' container orchestration systems. The flaw could allow attackers to escape container isolation and access host systems. All three major providers have released emergency patches and recommend immediate updates.",
    keyInsights: ["Affects AWS, Azure, and GCP", "Container escape vulnerability", "Emergency patches available", "No known active exploits yet"],
    sentiment: "negative",
    trending: true
  },
  {
    id: "8",
    title: "Brain-Computer Interface Allows Paralyzed Patient to Type 90 WPM",
    source: "Nature",
    url: "https://nature.com",
    publishedAt: "2025-10-16T10:00:00Z",
    imageUrl: "https://images.unsplash.com/photo-1668600372069-e39ec2ab28af?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiaW90ZWNoJTIwc2NpZW5jZSUyMGxhYm9yYXRvcnl8ZW58MXx8fHwxNzYwNzI4NzIwfDA&ixlib=rb-4.1.0&q=80&w=1080",
    category: ["Biotech", "AI/ML"],
    content: "Neuralink competitor achieves breakthrough in brain-computer interface speed...",
    summaryShort: "New BCI technology enables paralyzed patient to type at 90 words per minute.",
    summaryMedium: "A paralyzed patient using a next-generation brain-computer interface achieved typing speeds of 90 words per minute, nearly matching able-bodied typing speeds. The breakthrough comes from improved electrode design and machine learning algorithms that better decode neural signals. The technology could revolutionize communication for people with severe disabilities.",
    keyInsights: ["90 WPM typing speed achieved", "AI-powered neural signal decoding", "Non-invasive electrode design", "Clinical trials expanding to 50 patients"],
    sentiment: "positive",
    trending: false
  }
];

// Get all news articles with optional filtering
app.get("/make-server-3889d4d6/news", async (c) => {
  try {
    const categories = c.req.query("categories")?.split(",") || [];
    const search = c.req.query("search")?.toLowerCase() || "";
    const trending = c.req.query("trending") === "true";

    let filteredNews = [...MOCK_NEWS_DATA];

    // Filter by categories
    if (categories.length > 0) {
      filteredNews = filteredNews.filter(article =>
        article.category.some(cat => categories.includes(cat))
      );
    }

    // Filter by search
    if (search) {
      filteredNews = filteredNews.filter(article =>
        article.title.toLowerCase().includes(search) ||
        article.summaryMedium.toLowerCase().includes(search) ||
        article.content.toLowerCase().includes(search)
      );
    }

    // Filter by trending
    if (trending) {
      filteredNews = filteredNews.filter(article => article.trending);
    }

    // Add credibility scores and sources
    const articlesWithCredibility = filteredNews.map(article => ({
      ...article,
      credibilityScore: Math.floor(Math.random() * 30) + 70, // 70-100
      sourcesUsed: [article.source, "Reuters", "Associated Press"].slice(0, Math.floor(Math.random() * 2) + 1)
    }));

    return c.json({ articles: articlesWithCredibility });
  } catch (error) {
    console.log(`Error fetching news: ${error}`);
    return c.json({ error: "Failed to fetch news articles" }, 500);
  }
});

// Get user preferences
app.get("/make-server-3889d4d6/preferences", async (c) => {
  try {
    const userId = c.req.query("userId") || "default";
    const prefs = await kv.get(`user_prefs:${userId}`);
    
    if (!prefs) {
      // Default preferences
      return c.json({
        categories: ["AI/ML", "AI Agents"],
        digestFrequency: "daily"
      });
    }
    
    return c.json(prefs);
  } catch (error) {
    console.log(`Error fetching preferences: ${error}`);
    return c.json({ error: "Failed to fetch user preferences" }, 500);
  }
});

// Save user preferences
app.post("/make-server-3889d4d6/preferences", async (c) => {
  try {
    const userId = c.req.query("userId") || "default";
    const body = await c.req.json();
    
    await kv.set(`user_prefs:${userId}`, body);
    
    return c.json({ success: true });
  } catch (error) {
    console.log(`Error saving preferences: ${error}`);
    return c.json({ error: "Failed to save user preferences" }, 500);
  }
});

// Generate daily digest
app.get("/make-server-3889d4d6/digest", async (c) => {
  try {
    const userId = c.req.query("userId") || "default";
    const prefs = await kv.get(`user_prefs:${userId}`) || { categories: [] };
    
    let topNews = MOCK_NEWS_DATA
      .filter(article => 
        prefs.categories.length === 0 || 
        article.category.some(cat => prefs.categories.includes(cat))
      )
      .sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime())
      .slice(0, 5);
    
    const digest = {
      date: new Date().toISOString(),
      topStories: topNews,
      categoryBreakdown: {},
      trendingTopics: MOCK_NEWS_DATA.filter(a => a.trending).slice(0, 3)
    };
    
    // Calculate category breakdown
    MOCK_NEWS_DATA.forEach(article => {
      article.category.forEach(cat => {
        digest.categoryBreakdown[cat] = (digest.categoryBreakdown[cat] || 0) + 1;
      });
    });
    
    return c.json(digest);
  } catch (error) {
    console.log(`Error generating digest: ${error}`);
    return c.json({ error: "Failed to generate digest" }, 500);
  }
});

// Chat/Q&A endpoint (would integrate with OpenAI/Claude in production)
app.post("/make-server-3889d4d6/chat", async (c) => {
  try {
    const { question } = await c.req.json();
    
    // Mock response - in production, this would use GPT/Claude
    const mockResponse = {
      answer: `Based on recent tech news, I found several relevant articles about "${question}". The most significant development is the OpenAI GPT-5 announcement with 40% improvement in reasoning tasks. Would you like me to provide more details about any specific topic?`,
      relevantArticles: MOCK_NEWS_DATA.slice(0, 3).map(a => ({
        id: a.id,
        title: a.title,
        summaryShort: a.summaryShort
      }))
    };
    
    return c.json(mockResponse);
  } catch (error) {
    console.log(`Error processing chat request: ${error}`);
    return c.json({ error: "Failed to process chat request" }, 500);
  }
});

// Research endpoint - AI agent conducts research
app.post("/make-server-3889d4d6/research", async (c) => {
  try {
    const { query } = await c.req.json();
    
    const relevantArticles = MOCK_NEWS_DATA
      .filter(article => 
        article.title.toLowerCase().includes(query.toLowerCase().split(' ').slice(0, 2).join(' ')) ||
        article.category.some(cat => query.toLowerCase().includes(cat.toLowerCase()))
      )
      .slice(0, 5)
      .map(article => ({
        title: article.title,
        source: article.source,
        url: article.url,
        relevance: Math.random() * 0.4 + 0.6,
        summary: article.summaryMedium
      }));

    const report = {
      query,
      generatedAt: new Date().toISOString(),
      summary: `Our AI agent analyzed ${relevantArticles.length} articles across multiple sources to answer your query: "${query}". The research reveals significant developments in this area, with major announcements from industry leaders and emerging trends that could shape the future of technology.`,
      keyFindings: [
        `${relevantArticles.length} relevant articles found across ${new Set(relevantArticles.map(a => a.source)).size} different sources`,
        "Major tech companies are accelerating development in this space",
        "Industry experts predict significant market growth in the next 12-18 months",
        "Regulatory frameworks are still evolving to address new challenges",
        "Early adopters are reporting positive results and ROI"
      ],
      trending: [
        "AI/ML Integration",
        "Enterprise Adoption",
        "Regulatory Compliance",
        "Open Source Initiatives",
        "Venture Capital Interest"
      ],
      statistics: {
        articlesAnalyzed: relevantArticles.length,
        sourcesUsed: Array.from(new Set(relevantArticles.map(a => a.source))),
        timeRange: "Past 2 weeks"
      },
      articles: relevantArticles
    };
    
    return c.json(report);
  } catch (error) {
    console.log(`Error conducting research: ${error}`);
    return c.json({ error: "Failed to conduct research" }, 500);
  }
});

// Knowledge Graph endpoint
app.get("/make-server-3889d4d6/knowledge-graph", async (c) => {
  try {
    const nodes = [
      { id: "openai", name: "OpenAI", type: "company", connections: 5 },
      { id: "microsoft", name: "Microsoft", type: "company", connections: 4 },
      { id: "google", name: "Google", type: "company", connections: 4 },
      { id: "nvidia", name: "NVIDIA", type: "company", connections: 3 },
      { id: "apple", name: "Apple", type: "company", connections: 2 },
      { id: "tesla", name: "Tesla", type: "company", connections: 2 },
      { id: "sam-altman", name: "Sam Altman", type: "person", connections: 3 },
      { id: "satya-nadella", name: "Satya Nadella", type: "person", connections: 2 },
      { id: "jensen-huang", name: "Jensen Huang", type: "person", connections: 2 },
      { id: "gpt5", name: "GPT-5", type: "technology", connections: 3 },
      { id: "transformers", name: "Transformers", type: "technology", connections: 4 },
      { id: "cuda", name: "CUDA", type: "technology", connections: 2 },
      { id: "m4-chip", name: "M4 Chip", type: "technology", connections: 2 },
      { id: "optimus", name: "Optimus Robot", type: "technology", connections: 1 }
    ];

    const edges = [
      { source: "openai", target: "microsoft", relationship: "partnership" },
      { source: "openai", target: "sam-altman", relationship: "leadership" },
      { source: "openai", target: "gpt5", relationship: "develops" },
      { source: "microsoft", target: "satya-nadella", relationship: "leadership" },
      { source: "microsoft", target: "openai", relationship: "investor" },
      { source: "google", target: "transformers", relationship: "develops" },
      { source: "nvidia", target: "jensen-huang", relationship: "leadership" },
      { source: "nvidia", target: "cuda", relationship: "develops" },
      { source: "nvidia", target: "openai", relationship: "supplies" },
      { source: "apple", target: "m4-chip", relationship: "develops" },
      { source: "apple", target: "nvidia", relationship: "competes" },
      { source: "tesla", target: "optimus", relationship: "develops" },
      { source: "gpt5", target: "transformers", relationship: "based-on" },
      { source: "m4-chip", target: "nvidia", relationship: "competes" }
    ];
    
    return c.json({ nodes, edges });
  } catch (error) {
    console.log(`Error fetching knowledge graph: ${error}`);
    return c.json({ error: "Failed to fetch knowledge graph" }, 500);
  }
});

Deno.serve(app.fetch);