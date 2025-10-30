"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState({
    twilio: "",
    openai: "",
    elevenLabs: "",
  })

  const [voiceConfig, setVoiceConfig] = useState({
    voiceId: "rachel",
    speed: 1,
  })

  const [model, setModel] = useState("gpt-4")

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure integrations and preferences</p>
      </div>

      <Tabs defaultValue="api-keys" className="w-full">
        <TabsList>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="voice">Voice Configuration</TabsTrigger>
          <TabsTrigger value="model">Model Selection</TabsTrigger>
          <TabsTrigger value="company">Company Info</TabsTrigger>
        </TabsList>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage your integration API keys</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="twilio">Twilio API Key</Label>
                <Input
                  id="twilio"
                  type="password"
                  placeholder="Enter your Twilio API key"
                  value={apiKeys.twilio}
                  onChange={(e) => setApiKeys({ ...apiKeys, twilio: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="openai">OpenAI API Key</Label>
                <Input
                  id="openai"
                  type="password"
                  placeholder="Enter your OpenAI API key"
                  value={apiKeys.openai}
                  onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="elevenlabs">ElevenLabs API Key</Label>
                <Input
                  id="elevenlabs"
                  type="password"
                  placeholder="Enter your ElevenLabs API key"
                  value={apiKeys.elevenLabs}
                  onChange={(e) => setApiKeys({ ...apiKeys, elevenLabs: e.target.value })}
                />
              </div>

              <Button>Save API Keys</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Voice Configuration Tab */}
        <TabsContent value="voice" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Voice Configuration</CardTitle>
              <CardDescription>Configure voice settings for TTS</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="voice-id">Voice ID</Label>
                <Select
                  value={voiceConfig.voiceId}
                  onValueChange={(value) => setVoiceConfig({ ...voiceConfig, voiceId: value })}
                >
                  <SelectTrigger id="voice-id">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="rachel">Rachel</SelectItem>
                    <SelectItem value="clyde">Clyde</SelectItem>
                    <SelectItem value="domi">Domi</SelectItem>
                    <SelectItem value="bella">Bella</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="speed">Speech Speed</Label>
                <Input
                  id="speed"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={voiceConfig.speed}
                  onChange={(e) => setVoiceConfig({ ...voiceConfig, speed: Number.parseFloat(e.target.value) })}
                />
                <p className="text-sm text-muted-foreground">{voiceConfig.speed}x</p>
              </div>

              <Button>Save Voice Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Model Selection Tab */}
        <TabsContent value="model" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Selection</CardTitle>
              <CardDescription>Choose the AI model for your assistant</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="model">AI Model</Label>
                <Select value={model} onValueChange={setModel}>
                  <SelectTrigger id="model">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                    <SelectItem value="gpt-3.5">GPT-3.5 Turbo</SelectItem>
                    <SelectItem value="claude">Claude 3</SelectItem>
                    <SelectItem value="llama">Llama 2</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button>Save Model Selection</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Company Info Tab */}
        <TabsContent value="company" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Company Information</CardTitle>
              <CardDescription>Update your company details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="company-name">Company Name</Label>
                <Input id="company-name" placeholder="Your Company Name" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-email">Company Email</Label>
                <Input id="company-email" type="email" placeholder="contact@company.com" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-phone">Phone Number</Label>
                <Input id="company-phone" placeholder="+1 (555) 000-0000" />
              </div>

              <Button>Save Company Info</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
