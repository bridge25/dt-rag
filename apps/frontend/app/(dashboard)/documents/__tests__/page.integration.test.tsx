import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import DocumentsPage from "../page"
import * as api from "@/lib/api"

// Mock API
jest.mock("@/lib/api", () => ({
  uploadDocument: jest.fn(),
}))

describe("Documents Page Integration Tests", () => {
  let queryClient: QueryClient
  const mockUploadDocument = api.uploadDocument as jest.MockedFunction<typeof api.uploadDocument>

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    jest.clearAllMocks()
  })

  describe("File Selection", () => {
    it("should render file upload area", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      expect(screen.getByText(/upload documents/i)).toBeInTheDocument()
      expect(screen.getByText(/drag and drop files or click to select/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/click to upload/i)).toBeInTheDocument()
    })

    it("should add file to queue when selected via input", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test content"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText("test.txt")).toBeInTheDocument()
      })
    })

    it("should add multiple files to queue", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file1 = new File(["content1"], "file1.txt", { type: "text/plain" })
      const file2 = new File(["content2"], "file2.pdf", { type: "application/pdf" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, [file1, file2])

      await waitFor(() => {
        expect(screen.getByText("file1.txt")).toBeInTheDocument()
        expect(screen.getByText("file2.pdf")).toBeInTheDocument()
        expect(screen.getByText(/upload queue \(2\)/i)).toBeInTheDocument()
      })
    })
  })

  describe("Drag and Drop", () => {
    it("should highlight drop zone on drag over", async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const dropZone = screen.getByLabelText(/click to upload/i).closest("div")
      expect(dropZone).not.toHaveClass("border-orangePrimary")

      // Simulate drag over
      const dragEvent = new Event("dragover", { bubbles: true })
      Object.defineProperty(dragEvent, "dataTransfer", {
        value: { files: [] },
      })
      dropZone?.dispatchEvent(dragEvent)

      await waitFor(() => {
        expect(dropZone).toHaveClass("border-orangePrimary")
      })
    })

    it("should reset highlight on drag leave", async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const dropZone = screen.getByLabelText(/click to upload/i).closest("div")

      // Drag over
      const dragOverEvent = new Event("dragover", { bubbles: true })
      Object.defineProperty(dragOverEvent, "dataTransfer", { value: { files: [] } })
      dropZone?.dispatchEvent(dragOverEvent)

      await waitFor(() => {
        expect(dropZone).toHaveClass("border-orangePrimary")
      })

      // Drag leave
      const dragLeaveEvent = new Event("dragleave", { bubbles: true })
      Object.defineProperty(dragLeaveEvent, "dataTransfer", { value: { files: [] } })
      dropZone?.dispatchEvent(dragLeaveEvent)

      await waitFor(() => {
        expect(dropZone).not.toHaveClass("border-orangePrimary")
      })
    })

    it("should add files on drop", async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const dropZone = screen.getByLabelText(/click to upload/i).closest("div")
      const file = new File(["dropped content"], "dropped.txt", { type: "text/plain" })

      const dropEvent = new Event("drop", { bubbles: true })
      Object.defineProperty(dropEvent, "dataTransfer", {
        value: { files: [file] },
      })
      dropZone?.dispatchEvent(dropEvent)

      await waitFor(() => {
        expect(screen.getByText("dropped.txt")).toBeInTheDocument()
      })
    })
  })

  describe("File Upload", () => {
    it("should show uploading status during upload", async () => {
      mockUploadDocument.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ document_id: "doc-123" }), 100))
      )

      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      // Check uploading status
      await waitFor(() => {
        expect(screen.getByText("Uploading")).toBeInTheDocument()
      })
    })

    it("should show success status after successful upload", async () => {
      mockUploadDocument.mockResolvedValue({
        document_id: "doc-123",
        chunks_created: 5,
      })

      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText("Success")).toBeInTheDocument()
        expect(screen.getByText(/document id: doc-123/i)).toBeInTheDocument()
        expect(screen.getByText(/5 chunks created/i)).toBeInTheDocument()
      })
    })

    it("should show error status after failed upload", async () => {
      mockUploadDocument.mockRejectedValue(new Error("Upload failed: File too large"))

      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText("Failed")).toBeInTheDocument()
        expect(screen.getByText(/upload failed: file too large/i)).toBeInTheDocument()
      })
    })

    it("should show progress bar during upload", async () => {
      mockUploadDocument.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ document_id: "doc-123" }), 100))
      )

      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText("Processing document...")).toBeInTheDocument()
        expect(screen.getByRole("progressbar")).toBeInTheDocument()
      })
    })
  })

  describe("File Removal", () => {
    it("should remove file from queue when Remove button is clicked", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText("test.txt")).toBeInTheDocument()
      })

      const removeButton = screen.getByRole("button", { name: /remove/i })
      await user.click(removeButton)

      await waitFor(() => {
        expect(screen.queryByText("test.txt")).not.toBeInTheDocument()
      })
    })

    it("should update queue count after removing file", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file1 = new File(["test1"], "file1.txt", { type: "text/plain" })
      const file2 = new File(["test2"], "file2.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, [file1, file2])

      await waitFor(() => {
        expect(screen.getByText(/upload queue \(2\)/i)).toBeInTheDocument()
      })

      const removeButtons = screen.getAllByRole("button", { name: /remove/i })
      await user.click(removeButtons[0])

      await waitFor(() => {
        expect(screen.getByText(/upload queue \(1\)/i)).toBeInTheDocument()
      })
    })
  })

  describe("File Type Detection", () => {
    it("should display correct file type icon colors", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const pdfFile = new File(["pdf"], "test.pdf", { type: "application/pdf" })
      const txtFile = new File(["txt"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, [pdfFile, txtFile])

      await waitFor(() => {
        const fileIcons = screen.getAllByTestId(/file-type-icon-/)
        expect(fileIcons).toHaveLength(2)
      })
    })
  })

  describe("UI Queue Display", () => {
    it("should not show upload queue when no files are added", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      expect(screen.queryByText(/upload queue/i)).not.toBeInTheDocument()
    })

    it("should show upload queue card when files are added", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const file = new File(["test"], "test.txt", { type: "text/plain" })
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/upload queue \(1\)/i)).toBeInTheDocument()
        expect(screen.getByText(/track your document uploads in real-time/i)).toBeInTheDocument()
      })
    })

    it("should display correct file count in queue header", async () => {
      const user = userEvent.setup()

      render(
        <QueryClientProvider client={queryClient}>
          <DocumentsPage />
        </QueryClientProvider>
      )

      const files = [
        new File(["1"], "file1.txt", { type: "text/plain" }),
        new File(["2"], "file2.txt", { type: "text/plain" }),
        new File(["3"], "file3.txt", { type: "text/plain" }),
      ]
      const input = screen.getByLabelText(/click to upload/i) as HTMLInputElement

      await user.upload(input, files)

      await waitFor(() => {
        expect(screen.getByText(/upload queue \(3\)/i)).toBeInTheDocument()
      })
    })
  })
})
