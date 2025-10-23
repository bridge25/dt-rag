"use client";

import { useState, type DragEvent, type ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadDocument, deleteDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ModernCard } from "@/components/ui/modern-card";
import { IconBadge } from "@/components/ui/icon-badge";
import { Progress } from "@/components/ui/progress";
import { Tooltip } from "@/components/ui/tooltip";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Container } from "@/components/ui/container";
import { Stack } from "@/components/ui/stack";
import { Modal } from "@/components/ui/modal";
import { Upload, FileText, File, CheckCircle2, XCircle, AlertCircle, Trash2 } from "lucide-react";

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

const getFileTypeDescription = (fileName: string): string => {
  const ext = fileName.split(".").pop()?.toLowerCase()
  switch (ext) {
    case "pdf":
      return "PDF - Portable Document Format"
    case "docx":
    case "doc":
      return "DOCX - Microsoft Word Document"
    case "txt":
      return "TXT - Plain Text File"
    case "md":
      return "MD - Markdown Document"
    default:
      return "Unknown File Type"
  }
}

export default function DocumentsPage() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; documentId: string | null; fileName: string }>({
    isOpen: false,
    documentId: null,
    fileName: "",
  })

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

  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      return await deleteDocument(documentId)
    },
    onSuccess: (data) => {
      setFiles((prev) => prev.filter((f) => f.result?.document_id !== data.document_id))
      setDeleteModal({ isOpen: false, documentId: null, fileName: "" })
    },
    onError: (error) => {
      console.error("Failed to delete document:", error)
    },
  })

  const handleDeleteClick = (documentId: string, fileName: string) => {
    setDeleteModal({ isOpen: true, documentId, fileName })
  }

  const handleDeleteConfirm = () => {
    if (deleteModal.documentId) {
      deleteMutation.mutate(deleteModal.documentId)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteModal({ isOpen: false, documentId: null, fileName: "" })
  }

  return (
    <Container className="space-y-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-6">
      <Breadcrumb
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Documents", href: "/documents" }
        ]}
      />
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

          <Stack spacing="md" data-testid="file-list-stack">
            {files.map((uploadFile, index) => (
              <ModernCard key={`${uploadFile.file.name}-${index}`} variant="default" className="group">
                <div className="flex items-start gap-4">
                  <Tooltip content={getFileTypeDescription(uploadFile.file.name)} position="right">
                    <div data-testid={`file-type-icon-${index}`}>
                      <IconBadge
                        icon={FileText}
                        color={getFileTypeColor(uploadFile.file.name)}
                        size="md"
                      />
                    </div>
                  </Tooltip>

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
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <p className="text-xs font-medium text-green-800">
                              Document ID: {uploadFile.result.document_id}
                            </p>
                            {uploadFile.result.chunks_created && (
                              <p className="mt-1 text-xs text-green-700">
                                {uploadFile.result.chunks_created} chunks created
                              </p>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteClick(uploadFile.result!.document_id, uploadFile.file.name)}
                            className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                            data-testid="delete-document-button"
                          >
                            <Trash2 className="h-3 w-3" />
                            Delete
                          </Button>
                        </div>
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
              </ModernCard>
            ))}
          </Stack>
        </ModernCard>
      )}

      <Modal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        title="Delete Document"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Are you sure you want to delete <span className="font-semibold">{deleteModal.fileName}</span>?
          </p>
          <p className="text-sm text-gray-600">
            This action will permanently delete the document and all associated chunks. This cannot be undone.
          </p>
          <div className="flex gap-3 justify-end pt-4">
            <Button
              variant="outline"
              onClick={handleDeleteCancel}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </div>
      </Modal>
    </Container>
  );
}
