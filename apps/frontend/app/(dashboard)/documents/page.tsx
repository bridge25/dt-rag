"use client";

import { useState, type DragEvent, type ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, CheckCircle2, XCircle } from "lucide-react";

type UploadFile = {
  file: File
  progress: number
  status: "pending" | "uploading" | "success" | "error"
  result?: {
    document_id: string
    chunks_created?: number
  }
  error?: string
}

export default function DocumentsPage() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const mutation = useMutation({
    mutationFn: async (uploadFile: UploadFile) => {
      const result = await uploadDocument(
        {
          file_name: uploadFile.file.name,
          content_type: uploadFile.file.type,
        },
        uploadFile.file
      )
      return result
    },
    onSuccess: (data, uploadFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === uploadFile.file
            ? { ...f, status: "success", progress: 100, result: data }
            : f
        )
      )
    },
    onError: (error, uploadFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === uploadFile.file
            ? {
                ...f,
                status: "error",
                error: error instanceof Error ? error.message : "Upload failed",
              }
            : f
        )
      )
    },
  })

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      addFiles(selectedFiles)
    }
  }

  const addFiles = (newFiles: File[]) => {
    const uploadFiles: UploadFile[] = newFiles.map((file) => ({
      file,
      progress: 0,
      status: "pending",
    }))

    setFiles((prev) => [...prev, ...uploadFiles])

    uploadFiles.forEach((uploadFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === uploadFile.file ? { ...f, status: "uploading", progress: 50 } : f
        )
      )
      mutation.mutate(uploadFile)
    })
  }

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
        <p className="text-muted-foreground">
          Upload and manage your documents
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Drag and drop files or click to select
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50"
            }`}
          >
            <input
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              accept=".txt,.pdf,.docx,.md"
            />
            <label
              htmlFor="file-upload"
              className="flex flex-col items-center gap-2 cursor-pointer"
            >
              <Upload className="h-10 w-10 text-muted-foreground" />
              <div className="text-sm text-muted-foreground">
                <span className="font-semibold text-primary">
                  Click to upload
                </span>{" "}
                or drag and drop
              </div>
              <div className="text-xs text-muted-foreground">
                TXT, PDF, DOCX, MD (max 10MB each)
              </div>
            </label>
          </div>
        </CardContent>
      </Card>

      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Queue ({files.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {files.map((uploadFile, index) => (
              <div
                key={`${uploadFile.file.name}-${index}`}
                className="flex items-start gap-3 p-3 rounded-lg border"
              >
                <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium truncate">
                      {uploadFile.file.name}
                    </p>
                    {uploadFile.status === "success" && (
                      <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    )}
                    {uploadFile.status === "error" && (
                      <XCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                    )}
                  </div>

                  {uploadFile.status === "uploading" && (
                    <Progress value={uploadFile.progress} className="h-2" />
                  )}

                  {uploadFile.status === "success" && uploadFile.result && (
                    <div className="text-xs text-muted-foreground">
                      Document ID: {uploadFile.result.document_id}
                      {uploadFile.result.chunks_created && (
                        <> • {uploadFile.result.chunks_created} chunks created</>
                      )}
                    </div>
                  )}

                  {uploadFile.status === "error" && (
                    <p className="text-xs text-destructive">
                      {uploadFile.error}
                    </p>
                  )}
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(uploadFile.file)}
                  className="flex-shrink-0"
                >
                  Remove
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
