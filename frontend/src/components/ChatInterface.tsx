import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Send, Bot, User } from 'lucide-react';
import { Badge } from './ui/badge';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I\'m your AI assistant. Ask me anything about the tech news you\'ve been reading!',
    },
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const aiMessage: Message = {
        role: 'assistant',
        content: 'This is a placeholder response. In production, this would connect to your AI backend to provide intelligent answers based on the articles.',
      };
      setMessages((prev) => [...prev, aiMessage]);
    }, 1000);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="text-center">
        <h2 className="text-3xl font-display font-bold text-blue-600 mb-2">
          Ask AI
        </h2>
        <p className="text-gray-600">
          Get answers about any tech news topic
        </p>
      </div>

      {/* Main Chat Card - Yellow Background */}
      <div className="bg-yellow-300 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <Bot className="h-6 w-6 text-gray-700" />
          <h3 className="text-xl font-bold text-gray-900">AI Assistant</h3>
          <Badge className="ml-auto bg-blue-500 text-white">Online</Badge>
        </div>

        {/* Messages Area */}
        <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 mb-4 min-h-[400px] max-h-[500px] overflow-y-auto space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full gradient-primary flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-gray-100 text-foreground'
                }`}
              >
                {message.content}
              </div>


              {message.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything..."
            className="flex-1 bg-white"
          />
          <Button onClick={handleSend} className="bg-blue-600 hover:bg-blue-700 text-white">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
