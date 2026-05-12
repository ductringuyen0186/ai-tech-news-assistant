import { useState } from "react";
import { MessageCircle, Send, Bot, User, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { MarkdownReport } from "./MarkdownReport";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  relevantArticles?: Array<{
    id: string;
    title: string;
    summaryShort: string;
    /**
     * Canonical URL of the source article. The chat bubble wraps each
     * related-article card in an `<a href={url} target="_blank">` so users
     * can click through to the source. Empty string means we render the
     * card as a non-link fallback (still readable, just not clickable).
     */
    url?: string;
  }>;
}

interface ChatInterfaceProps {
  onAskQuestion: (question: string) => Promise<any>;
}

export function ChatInterface({ onAskQuestion }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hi! I'm your AI tech news assistant. Ask me anything about recent tech news, trends, or specific topics like AI, biotech, or military technology.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await onAskQuestion(input);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        relevantArticles: response.relevantArticles,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your question. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 gradient-primary rounded-full flex items-center justify-center shadow-md">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle>Ask About Tech News</CardTitle>
            <CardDescription>
              Conversational search powered by AI
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent
        className="flex-1 flex flex-col p-0 overflow-hidden"
        style={{ minHeight: 0, height: "100%" }}
      >
        <div
          className="flex-1 p-4"
          style={{ minHeight: 0, height: 0, overflowY: "auto" }}
        >
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 min-w-0 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 gradient-primary rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}

                <div
                  className={`max-w-[80%] min-w-0 rounded-lg p-3 break-words ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                  style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
                >
                  {message.role === "assistant" ? (
                    <MarkdownReport text={message.content} linkifyCitations />
                  ) : (
                    <p className="text-sm whitespace-pre-wrap break-words" style={{ overflowWrap: "anywhere" }}>{message.content}</p>
                  )}
                  
                  {message.relevantArticles && message.relevantArticles.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300 space-y-2">
                      <p className="text-xs text-gray-600 mb-2">
                        Related articles:
                      </p>
                      {message.relevantArticles.map((article) => {
                        const hasUrl =
                          typeof article.url === "string" && article.url.length > 0;
                        const cardClass =
                          "bg-white p-2 rounded text-xs text-gray-800 block transition-colors " +
                          (hasUrl
                            ? "cursor-pointer hover:bg-blue-50 hover:text-blue-700"
                            : "");
                        const titleClass =
                          "mb-1 " +
                          (hasUrl ? "underline-offset-2 hover:underline" : "");
                        const inner = (
                          <>
                            <p className={titleClass}>{article.title}</p>
                            {article.summaryShort && (
                              <p className="text-gray-600">
                                {article.summaryShort}
                              </p>
                            )}
                          </>
                        );
                        if (hasUrl) {
                          return (
                            <a
                              key={article.id || article.url}
                              href={article.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={cardClass}
                            >
                              {inner}
                            </a>
                          );
                        }
                        return (
                          <div key={article.id} className={cardClass}>
                            {inner}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {message.role === "user" && (
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about tech news..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
          <div className="mt-2 flex flex-wrap gap-2">
            <p className="text-xs text-gray-500 w-full">Try asking:</p>
            <Badge
              variant="outline"
              className="cursor-pointer text-xs hover:bg-gray-100"
              onClick={() => setInput("What's new with OpenAI?")}
            >
              What's new with OpenAI?
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer text-xs hover:bg-gray-100"
              onClick={() => setInput("Latest biotech breakthroughs")}
            >
              Latest biotech breakthroughs
            </Badge>
            <Badge
              variant="outline"
              className="cursor-pointer text-xs hover:bg-gray-100"
              onClick={() => setInput("AI safety news this week")}
            >
              AI safety news this week
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}