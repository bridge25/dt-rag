import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import DocumentsPage from "../page"
import { uploadDocument } from "@/lib/api"

jest.mock("@/lib/api", () => ({
  uploadDocument: jest.fn(),
}))

const mockUploadDocument = uploadDocument as jest.MockedFunction<typeof uploadDocument>

describe("@TEST:TOOLTIP-INTEGRATION - Tooltip Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUploadDocument.mockResolvedValue({
      document_id: "test-doc-id",
      chunks_created: 10,
    })
  })
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  it("should show tooltip on file icon hover", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentsPage />
      </QueryClientProvider>
    )

    const fileInput = screen.getByLabelText(/click to upload/i)
    const testFile = new File(["content"], "sample.pdf", { type: "application/pdf" })

    await userEvent.upload(fileInput, testFile)

    await waitFor(() => {
      expect(screen.getByText("sample.pdf")).toBeInTheDocument()
    })

    const icon = screen.getByTestId("file-type-icon-0")

    await userEvent.hover(icon)

    await waitFor(
      () => {
        expect(screen.getByText("PDF - Portable Document Format")).toBeInTheDocument()
      },
      { timeout: 500 }
    )
  })

  it("should hide tooltip on mouse out", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentsPage />
      </QueryClientProvider>
    )

    const fileInput = screen.getByLabelText(/click to upload/i)
    const testFile = new File(["content"], "sample.pdf", { type: "application/pdf" })

    await userEvent.upload(fileInput, testFile)

    await waitFor(() => {
      expect(screen.getByText("sample.pdf")).toBeInTheDocument()
    })

    const icon = screen.getByTestId("file-type-icon-0")

    await userEvent.hover(icon)
    await waitFor(() => {
      expect(screen.getByText("PDF - Portable Document Format")).toBeInTheDocument()
    })

    await userEvent.unhover(icon)

    await waitFor(() => {
      expect(screen.queryByText("PDF - Portable Document Format")).not.toBeInTheDocument()
    })
  })
})
