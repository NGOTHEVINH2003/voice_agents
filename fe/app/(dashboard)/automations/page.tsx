"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, Edit2, Trash2, Play } from "lucide-react"

const mockAutomations = [
  {
    id: 1,
    name: "Generate Daily Report",
    trigger: "Daily at 9:00 AM",
    actions: ["Fetch data from CRM", "Generate PDF", "Send email"],
    status: "active",
    lastRun: "2 hours ago",
  },
  {
    id: 2,
    name: "Sync CRM Data",
    trigger: "Every 30 minutes",
    actions: ["Pull from Salesforce", "Update database"],
    status: "active",
    lastRun: "5 minutes ago",
  },
  {
    id: 3,
    name: "Customer Feedback Summary",
    trigger: "Weekly on Monday",
    actions: ["Collect feedback", "Analyze sentiment", "Post to Slack"],
    status: "inactive",
    lastRun: "Never",
  },
]

export default function AutomationsPage() {
  const [automations, setAutomations] = useState(mockAutomations)

  return (
    <div className="space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Automations</h1>
          <p className="text-muted-foreground">Create and manage workflow automations</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Automation
        </Button>
      </div>

      <div className="space-y-4">
        {automations.map((automation) => (
          <Card key={automation.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle>{automation.name}</CardTitle>
                  <CardDescription>{automation.trigger}</CardDescription>
                </div>
                <Badge variant={automation.status === "active" ? "default" : "secondary"}>{automation.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">Actions:</p>
                  <div className="flex flex-wrap gap-2">
                    {automation.actions.map((action, idx) => (
                      <Badge key={idx} variant="outline">
                        {action}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">Last run: {automation.lastRun}</p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Play className="h-4 w-4 mr-1" />
                      Run Now
                    </Button>
                    <Button variant="outline" size="sm">
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
