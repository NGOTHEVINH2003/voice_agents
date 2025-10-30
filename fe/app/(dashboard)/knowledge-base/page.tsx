"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, Trash2, Search } from "lucide-react"

const mockDocuments = [
  {
    id: 1,
    name: "Company Policies.pdf",
    type: "PDF",
    size: "2.4 MB",
    uploadedAt: "2 days ago",
    embeddingProgress: 100,
  },
  {
    id: 2,
    name: "Product Catalog.csv",
    type: "CSV",
    size: "1.8 MB",
    uploadedAt: "1 week ago",
    embeddingProgress: 100,
  },
  {
    id: 3,
    name: "FAQ Document.docx",
    type: "DOC",
    size: "0.5 MB",
    uploadedAt: "3 days ago",
    embeddingProgress: 85,
  },
]

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState(mockDocuments)
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <p className="text-muted-foreground">Upload and manage documents for RAG</p>
        </div>
        <Button>
          <Upload className="h-4 w-4 mr-2" />
          Upload Document
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search knowledge base..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Documents List */}
      <div className="space-y-4">
        {documents.map((doc) => (
          <Card key={doc.id}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <h3 className="font-medium">{doc.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    {doc.type} • {doc.size} • Uploaded {doc.uploadedAt}
                  </p>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span>Embedding Progress</span>
                      <span>{doc.embeddingProgress}%</span>
                    </div>
                    <Progress value={doc.embeddingProgress} className="h-2" />
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
