"use client";

import { useState, type DragEvent, type ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ModernCard } from "@/components/ui/modern-card";
import { IconBadge } from "@/components/ui/icon-badge";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, File, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

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

const getFileTypeColor = (fileName: string): "red" | "blue" | "green" | "purple" => {
  const ext = fileName.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "pdf":
      return "red";
    case "docx":
    case "doc":
      return "blue";
    case "txt":
      return "green";
    case "md":
      return "purple";
    default:
      return "blue";
  }
};

export default function DocumentsPage() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const mutation = useMutation({
    mutationFn: async (uploadFile: UploadFile) => {
      const formData = new FormData()
      formData.append("file", uploadFile.file)
      formData.append("file_name", uploadFile.file.name)
      formData.append("content_type", uploadFile.file.type)
      const result = await uploadDocument(formData)
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
    <div className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Documents</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Upload and manage your documents
        </p>
      </div>

      <ModernCard variant="beige">
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-gray-900">Upload Documents</h3>
          <p className="mt-1 text-sm text-gray-600">
            Drag and drop files or click to select
          </p>
        </div>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragging
              ? "border-orangePrimary bg-orangePrimary/10 scale-[1.02]"
              : "border-gray-300 hover:border-orangePrimary/50 hover:bg-gray-50"
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
            className="flex flex-col items-center gap-4 cursor-pointer"
          >
            <IconBadge icon={Upload} color="orange" size="lg" />
            <div className="text-base text-gray-700">
              <span className="font-bold text-orangePrimary">
                Click to upload
              </span>{" "}
              or drag and drop
            </div>
            <div className="text-sm text-gray-500">
              TXT, PDF, DOCX, MD (max 10MB each)
            </div>
          </label>
        </div>
      </ModernCard>

      {files.length > 0 && (
        <ModernCard variant="teal">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-gray-900">
              Upload Queue ({files.length})
            </h3>
            <p className="mt-1 text-sm text-gray-600">
              Track your document uploads in real-time
            </p>
          </div>

          <div className="space-y-4">
            {files.map((uploadFile, index) => (
              <div
                key={`${uploadFile.file.name}-${index}`}
                className="group rounded-xl bg-white p-4 shadow-sm transition-all duration-300 hover:shadow-md hover:scale-[1.01]"
              >
                <div className="flex items-start gap-4">
                  <IconBadge
                    icon={FileText}
                    color={getFileTypeColor(uploadFile.file.name)}
                    size="md"
                  />

                  <div className="flex-1 min-w-0 space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-base font-semibold text-gray-900 truncate">
                        {uploadFile.file.name}
                      </p>
                      {uploadFile.status === "success" && (
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs font-medium text-green-600">Success</span>
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        </div>
                      )}
                      {uploadFile.status === "error" && (
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs font-medium text-red-600">Failed</span>
                          <XCircle className="h-5 w-5 text-red-500" />
                        </div>
                      )}
                      {uploadFile.status === "uploading" && (
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs font-medium text-blue-600">Uploading</span>
                          <AlertCircle className="h-5 w-5 text-blue-500 animate-pulse" />
                        </div>
                      )}
                    </div>

                    {uploadFile.status === "uploading" && (
                      <div className="space-y-1">
                        <Progress value={uploadFile.progress} className="h-2" />
                        <p className="text-xs text-gray-500">
                          Processing document...
                        </p>
                      </div>
                    )}

                    {uploadFile.status === "success" && uploadFile.result && (
                      <div className="rounded-lg bg-green-50 p-3">
                        <p className="text-xs font-medium text-green-800">
                          Document ID: {uploadFile.result.document_id}
                        </p>
                        {uploadFile.result.chunks_created && (
                          <p className="mt-1 text-xs text-green-700">
                            {uploadFile.result.chunks_created} chunks created
                          </p>
                        )}
                      </div>
                    )}

                    {uploadFile.status === "error" && (
                      <div className="rounded-lg bg-red-50 p-3">
                        <p className="text-xs font-medium text-red-800">
                          {uploadFile.error}
                        </p>
                      </div>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(uploadFile.file)}
                    className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </ModernCard>
      )}
    </div>
  );
}
