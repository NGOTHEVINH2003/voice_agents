"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { Mic, Upload, Zap } from "lucide-react"

const dailyUsageData = [
  { date: "Mon", conversations: 45, automations: 32 },
  { date: "Tue", conversations: 52, automations: 38 },
  { date: "Wed", conversations: 48, automations: 35 },
  { date: "Thu", conversations: 61, automations: 42 },
  { date: "Fri", conversations: 55, automations: 40 },
  { date: "Sat", conversations: 38, automations: 28 },
  { date: "Sun", conversations: 42, automations: 31 },
]

const sentimentData = [
  { name: "Positive", value: 65, fill: "#10b981" },
  { name: "Neutral", value: 25, fill: "#6b7280" },
  { name: "Negative", value: 10, fill: "#ef4444" },
]

export default function DashboardPage() {
  return (
    <div className="space-y-8 p-8">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">+12% from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Automated Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">156</div>
            <p className="text-xs text-muted-foreground">+8% from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">Connected integrations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">99.8%</div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily Usage</CardTitle>
            <CardDescription>Conversations and automations over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyUsageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="conversations" stroke="#4f46e5" strokeWidth={2} />
                <Line type="monotone" dataKey="automations" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Customer Sentiment</CardTitle>
            <CardDescription>Distribution of conversation sentiments</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name} ${value}%`}
                  outerRadius={80}
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks and operations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Button className="h-24 flex flex-col items-center justify-center gap-2 bg-transparent" variant="outline">
              <Mic className="h-6 w-6" />
              <span>Start Voice Call</span>
            </Button>
            <Button className="h-24 flex flex-col items-center justify-center gap-2 bg-transparent" variant="outline">
              <Upload className="h-6 w-6" />
              <span>Upload Document</span>
            </Button>
            <Button className="h-24 flex flex-col items-center justify-center gap-2 bg-transparent" variant="outline">
              <Zap className="h-6 w-6" />
              <span>Run Automation</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
