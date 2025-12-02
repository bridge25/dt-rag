/**
 * ImportKnowledgeModal - Document upload modal for Taxonomy page
 * Reuses upload logic from Documents page
 *
 * @CODE:FRONTEND-REDESIGN-001-IMPORT-MODAL
 */

"use client";

import { useState, useEffect, type DragEvent, type ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  X,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

type UploadFile = {
  file: File;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  result?: {
    document_id: string;
    chunks_created?: number;
  };
  error?: string;
};

interface ImportKnowledgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete?: (results: { document_id: string }[]) => void;
}

export function ImportKnowledgeModal({
  isOpen,
  onClose,
  onUploadComplete,
}: ImportKnowledgeModalProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  // ESC key handler
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Reset files when modal closes
  useEffect(() => {
    if (!isOpen) {
      setFiles([]);
    }
  }, [isOpen]);

  const mutation = useMutation({
    mutationFn: async (uploadFile: UploadFile) => {
      const formData = new FormData();
      formData.append("file", uploadFile.file);
      formData.append("file_name", uploadFile.file.name);
      formData.append("content_type", uploadFile.file.type);
      const result = await uploadDocument(formData);
      return result;
    },
    onSuccess: (data, uploadFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === uploadFile.file
            ? { ...f, status: "success", progress: 100, result: data }
            : f
        )
      );
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
      );
    },
  });

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  };

  const addFiles = (newFiles: File[]) => {
    const uploadFiles: UploadFile[] = newFiles.map((file) => ({
      file,
      progress: 0,
      status: "pending",
    }));

    setFiles((prev) => [...prev, ...uploadFiles]);

    uploadFiles.forEach((uploadFile) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.file === uploadFile.file
            ? { ...f, status: "uploading", progress: 50 }
            : f
        )
      );
      mutation.mutate(uploadFile);
    });
  };

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const handleComplete = () => {
    const successfulUploads = files
      .filter((f) => f.status === "success" && f.result)
      .map((f) => ({ document_id: f.result!.document_id }));

    if (onUploadComplete && successfulUploads.length > 0) {
      onUploadComplete(successfulUploads);
    }
    onClose();
  };

  const hasSuccessfulUploads = files.some((f) => f.status === "success");
  const allComplete = files.length > 0 && files.every((f) => f.status === "success" || f.status === "error");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl mx-4 animate-in fade-in zoom-in-95 duration-300">
        <div className="bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl shadow-cyan-500/10 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-cyan-400/10 border border-cyan-400/20">
                <Sparkles className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Import Knowledge</h2>
                <p className="text-xs text-gray-400">
                  Add documents to expand your taxonomy
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Upload Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={cn(
                "relative group overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-300",
                isDragging
                  ? "border-cyan-400 bg-cyan-400/10 scale-[1.01]"
                  : "border-white/10 bg-white/5 hover:border-cyan-400/30"
              )}
            >
              <div className="relative p-8 text-center cursor-pointer">
                <input
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  id="modal-file-upload"
                  accept=".txt,.pdf,.docx,.md"
                />
                <label
                  htmlFor="modal-file-upload"
                  className="flex flex-col items-center gap-4 cursor-pointer"
                >
                  <div
                    className={cn(
                      "p-4 rounded-full bg-white/5 border border-white/10 transition-all duration-300",
                      isDragging && "bg-cyan-400/20 border-cyan-400"
                    )}
                  >
                    <Upload
                      className={cn(
                        "w-8 h-8 transition-colors",
                        isDragging ? "text-cyan-400" : "text-gray-400"
                      )}
                    />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-white">
                      <span className="text-cyan-400">Click to upload</span> or
                      drag and drop
                    </p>
                    <p className="text-xs text-gray-500 font-mono">
                      PDF, DOCX, TXT, MD
                    </p>
                  </div>
                </label>
              </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar">
                {files.map((uploadFile, index) => (
                  <div
                    key={`${uploadFile.file.name}-${index}`}
                    className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5"
                  >
                    <div
                      className={cn(
                        "p-2 rounded-lg",
                        uploadFile.status === "success"
                          ? "bg-cyan-400/10"
                          : uploadFile.status === "error"
                          ? "bg-red-500/10"
                          : "bg-white/5"
                      )}
                    >
                      <FileText
                        className={cn(
                          "w-4 h-4",
                          uploadFile.status === "success"
                            ? "text-cyan-400"
                            : uploadFile.status === "error"
                            ? "text-red-400"
                            : "text-gray-400"
                        )}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {uploadFile.file.name}
                      </p>
                      {uploadFile.status === "uploading" && (
                        <div className="mt-1">
                          <Progress
                            value={uploadFile.progress}
                            className="h-1 bg-white/5"
                          />
                        </div>
                      )}
                      {uploadFile.status === "success" && (
                        <p className="text-xs text-cyan-400 flex items-center gap-1 mt-0.5">
                          <CheckCircle2 className="w-3 h-3" />
                          Indexed
                        </p>
                      )}
                      {uploadFile.status === "error" && (
                        <p className="text-xs text-red-400 truncate mt-0.5">
                          {uploadFile.error}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => removeFile(uploadFile.file)}
                      className="p-1 text-gray-500 hover:text-white transition-colors"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-white/5 bg-white/5">
            <p className="text-xs text-gray-400">
              {files.length > 0
                ? `${files.filter((f) => f.status === "success").length}/${files.length} uploaded`
                : "No files selected"}
            </p>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={onClose}
                className="border-white/10 text-gray-300 hover:bg-white/5"
              >
                Cancel
              </Button>
              <Button
                onClick={handleComplete}
                disabled={!hasSuccessfulUploads}
                className="bg-gradient-to-r from-cyan-500 to-purple-500 text-white hover:opacity-90 disabled:opacity-50"
              >
                {allComplete ? "Done" : "Complete"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
