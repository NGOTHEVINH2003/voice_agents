"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Mic, Send, Phone } from "lucide-react"

const mockConversations = [
  {
    id: 1,
    customer: "John Doe",
    type: "chat",
    lastMessage: "Can you help me with my order?",
    timestamp: "2 min ago",
    sentiment: "neutral",
  },
  {
    id: 2,
    customer: "Jane Smith",
    type: "voice",
    lastMessage: "Voice call ended",
    timestamp: "15 min ago",
    sentiment: "positive",
  },
  {
    id: 3,
    customer: "Bob Johnson",
    type: "chat",
    lastMessage: "Thank you for the assistance!",
    timestamp: "1 hour ago",
    sentiment: "positive",
  },
]

export default function ConversationsPage() {
  const [selectedConversation, setSelectedConversation] = useState(mockConversations[0])
  const [messages, setMessages] = useState([
    { id: 1, sender: "customer", text: "Can you help me with my order?" },
    { id: 2, sender: "ai", text: "Of course! I'd be happy to help. What's your order number?" },
    { id: 3, sender: "customer", text: "It's #12345" },
  ])
  const [inputValue, setInputValue] = useState("")

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      setMessages([...messages, { id: messages.length + 1, sender: "ai", text: inputValue }])
      setInputValue("")
    }
  }

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Conversations</h1>
        <p className="text-muted-foreground">Manage live chat and voice interactions</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {/* Conversation List */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Active Conversations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {mockConversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedConversation(conv)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedConversation.id === conv.id ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{conv.customer}</p>
                    <p className="text-sm truncate opacity-75">{conv.lastMessage}</p>
                  </div>
                  {conv.type === "voice" && <Phone className="h-4 w-4" />}
                </div>
                <p className="text-xs opacity-50 mt-1">{conv.timestamp}</p>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Chat/Voice Panel */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>{selectedConversation.customer}</CardTitle>
            <CardDescription>
              {selectedConversation.type === "voice" ? "Voice Call" : "Chat Conversation"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col h-96">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender === "ai" ? "justify-start" : "justify-end"}`}>
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg ${
                      msg.sender === "ai" ? "bg-muted text-muted-foreground" : "bg-primary text-primary-foreground"
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <Input
                placeholder="Type your message..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
              />
              <Button onClick={handleSendMessage} size="icon">
                <Send className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon">
                <Mic className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
