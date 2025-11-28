/**
 * Documents page - Digital Archive
 * Ethereal Glass Theme Applied
 *
 * @CODE:FRONTEND-REDESIGN-001-DOCUMENTS
 */

"use client";

import { useState, type DragEvent, type ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, File, CheckCircle2, XCircle, AlertCircle, Archive, HardDrive, Cloud } from "lucide-react";
import { cn } from "@/lib/utils";

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

const _getFileTypeColor = (fileName: string): "red" | "blue" | "green" | "purple" => {
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
    <div className="min-h-[calc(100vh-4rem)] relative overflow-hidden p-8">
      {/* Ambient Background - Cyan Nebula */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-cyan-500/5 blur-[100px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-purple-500/5 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md shadow-[0_0_15px_rgba(0,247,255,0.2)]">
                <Archive className="w-6 h-6 text-cyan-400" />
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-white drop-shadow-[0_0_10px_rgba(0,247,255,0.3)]">Digital Archive</h1>
            </div>
            <p className="text-gray-400 max-w-xl">
              Securely ingest and index your knowledge base documents.
            </p>
          </div>

          <div className="flex items-center gap-4 px-4 py-2 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-mono text-gray-300">STORAGE</span>
            </div>
            <div className="h-4 w-[1px] bg-white/10" />
            <div className="flex items-center gap-2">
              <Cloud className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-mono text-cyan-400">CONNECTED</span>
            </div>
          </div>
        </div>

        {/* Upload Zone - Ethereal Glass */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "relative group overflow-hidden rounded-3xl border-2 border-dashed transition-all duration-500",
            isDragging
              ? "border-cyan-400 bg-cyan-400/10 scale-[1.01] shadow-[0_0_30px_rgba(0,247,255,0.3)]"
              : "border-white/10 bg-white/5 hover:border-cyan-400/30 hover:bg-white/10"
          )}
        >
          {/* Scanning Effect */}
          <div className={cn(
            "absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400/10 to-transparent pointer-events-none transition-transform duration-1000",
            isDragging ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0"
          )} />

          <div className="relative p-16 text-center cursor-pointer">
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
              className="flex flex-col items-center gap-6 cursor-pointer"
            >
              <div className={cn(
                "p-6 rounded-full bg-white/5 border border-white/10 transition-all duration-300 group-hover:scale-110 group-hover:shadow-[0_0_25px_rgba(0,247,255,0.4)]",
                isDragging && "shadow-[0_0_30px_rgba(0,247,255,0.5)] scale-110 bg-cyan-400/20 border-cyan-400"
              )}>
                <Upload className={cn(
                  "w-10 h-10 transition-colors duration-300",
                  isDragging ? "text-cyan-400" : "text-gray-400 group-hover:text-cyan-400"
                )} />
              </div>

              <div className="space-y-2">
                <p className="text-xl font-medium text-white">
                  <span className="text-cyan-400 font-bold drop-shadow-[0_0_8px_rgba(0,247,255,0.6)]">Click to upload</span> or drag and drop
                </p>
                <p className="text-sm text-gray-500 font-mono">
                  SUPPORTED FORMATS: PDF, DOCX, TXT, MD
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* File Grid - Ethereal Glass */}
        {files.length > 0 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between px-2">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Processing Queue
                <span className="px-2 py-0.5 rounded-full bg-cyan-400/10 text-xs font-mono text-cyan-400 border border-cyan-400/20">
                  {files.length}
                </span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {files.map((uploadFile, index) => (
                <div
                  key={`${uploadFile.file.name}-${index}`}
                  className="group relative p-4 rounded-2xl bg-white/5 backdrop-blur-lg border border-white/10 hover:border-cyan-400/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(0,247,255,0.3)]"
                >
                  <div className="flex items-start gap-4">
                    <div className={cn(
                      "p-3 rounded-xl border transition-colors",
                      uploadFile.status === "success" ? "bg-cyan-400/10 border-cyan-400/20" :
                        uploadFile.status === "error" ? "bg-red-500/10 border-red-500/20" :
                          "bg-white/5 border-white/10"
                    )}>
                      <FileText className={cn(
                        "w-6 h-6",
                        uploadFile.status === "success" ? "text-cyan-400" :
                          uploadFile.status === "error" ? "text-red-400" :
                            "text-gray-400"
                      )} />
                    </div>

                    <div className="flex-1 min-w-0 space-y-2">
                      <div className="flex items-start justify-between">
                        <p className="text-sm font-medium text-white truncate pr-2">
                          {uploadFile.file.name}
                        </p>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFile(uploadFile.file)}
                          className="h-6 w-6 -mt-1 -mr-1 text-gray-500 hover:text-white hover:bg-white/10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* Status Indicators */}
                      {uploadFile.status === "uploading" && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs text-gray-400">
                            <span className="flex items-center gap-1">
                              <AlertCircle className="w-3 h-3 animate-pulse text-cyan-400" />
                              Uploading...
                            </span>
                            <span className="font-mono">{uploadFile.progress}%</span>
                          </div>
                          <Progress value={uploadFile.progress} className="h-1 bg-white/5" />
                        </div>
                      )}

                      {uploadFile.status === "success" && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-1.5 text-xs text-cyan-400">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span className="font-medium">Indexed Successfully</span>
                          </div>
                          {uploadFile.result && (
                            <div className="px-2 py-1 rounded bg-white/5 border border-white/5 text-[10px] font-mono text-gray-400 truncate">
                              ID: {uploadFile.result.document_id}
                            </div>
                          )}
                        </div>
                      )}

                      {uploadFile.status === "error" && (
                        <div className="flex items-start gap-1.5 text-xs text-red-400">
                          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                          <span className="line-clamp-2">{uploadFile.error}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Bottom glow bar */}
                  <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
