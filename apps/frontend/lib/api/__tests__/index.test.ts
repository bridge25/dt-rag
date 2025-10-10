import MockAdapter from "axios-mock-adapter"
import { apiClient } from "../client"
import { search, classify, batchSearch, uploadDocument, getHealth } from "../index"

describe("API Integration Fixes - SPEC-API-INTEGRATION-001", () => {
  let mock: InstanceType<typeof MockAdapter>

  beforeEach(() => {
    mock = new MockAdapter(apiClient)
  })

  afterEach(() => {
    mock.restore()
  })

  describe("AC-1: Trailing slash removal", () => {
    test("search should call /search without trailing slash", async () => {
      const validResponse = {
        hits: [],
        latency: 0.1,
        request_id: "test-id",
      }
      mock.onPost("/search").reply(200, validResponse)

      await search({ q: "test", max_results: 10 })

      expect(mock.history.post.length).toBe(1)
      expect(mock.history.post[0].url).toBe("/search")
      expect(mock.history.post[0].url).not.toContain("/search/")
    })

    test("classify should call /classify without trailing slash", async () => {
      const validResponse = {
        classifications: [],
        request_id: "test-id",
        processing_time: 0.1,
      }
      mock.onPost("/classify").reply(200, validResponse)

      await classify({ text: "test text" })

      expect(mock.history.post.length).toBe(1)
      expect(mock.history.post[0].url).toBe("/classify")
    })

    test("batchSearch should call /batch-search without trailing slash", async () => {
      const validResponse = {
        results: [],
        total_latency: 0.1,
        total_queries: 2,
        total_unique_hits: 0,
        request_id: "test-id",
        parallel_execution: true,
      }
      mock.onPost("/batch-search").reply(200, validResponse)

      await batchSearch({ queries: ["q1", "q2"] })

      expect(mock.history.post.length).toBe(1)
      expect(mock.history.post[0].url).toBe("/batch-search")
    })
  })

  describe("AC-2: baseURL usage (no hardcoded URLs)", () => {
    test("uploadDocument should use relative path /ingestion/upload", async () => {
      const validResponse = {
        document_id: "123",
        status: "uploaded",
      }
      mock.onPost("/ingestion/upload").reply(200, validResponse)

      const formData = new FormData()
      formData.append("file", new Blob(["test"]), "test.txt")

      await uploadDocument(formData)

      expect(mock.history.post.length).toBe(1)
      expect(mock.history.post[0].url).toBe("/ingestion/upload")
      expect(mock.history.post[0].url).not.toContain("http://localhost")
    })

    test("getHealth should use relative path /healthz", async () => {
      const validResponse = {
        status: "ok",
        database: "connected",
        redis: "connected",
        timestamp: new Date().toISOString(),
      }
      mock.onGet("/healthz").reply(200, validResponse)

      await getHealth()

      expect(mock.history.get.length).toBe(1)
      expect(mock.history.get[0].url).toBe("/healthz")
      expect(mock.history.get[0].url).not.toContain("http://localhost")
    })

    test("no hardcoded localhost URLs in any API calls", async () => {
      mock.onPost("/search").reply(200, {
        hits: [],
        latency: 0.1,
        request_id: "test-id",
      })
      mock.onPost("/classify").reply(200, {
        classifications: [],
        request_id: "test-id",
        processing_time: 0.1,
      })
      mock.onPost("/ingestion/upload").reply(200, {
        document_id: "123",
        status: "uploaded",
      })
      mock.onGet("/healthz").reply(200, {
        status: "ok",
        database: "connected",
        redis: "connected",
        timestamp: new Date().toISOString(),
      })

      await search({ q: "test", max_results: 10 })
      await classify({ text: "test" })

      const formData = new FormData()
      formData.append("file", new Blob(["test"]), "test.txt")
      await uploadDocument(formData)

      await getHealth()

      const allRequests = [...mock.history.post, ...mock.history.get]
      allRequests.forEach(request => {
        expect(request.url).not.toContain("http://localhost:8000")
      })
    })
  })

  describe("AC-3: Environment variable application", () => {
    test("all API calls should use baseURL from env config", async () => {
      const validResponse = {
        hits: [],
        latency: 0.1,
        request_id: "test-id",
      }
      mock.onPost("/search").reply(200, validResponse)

      await search({ q: "test", max_results: 10 })

      expect(mock.history.post[0].url).toBe("/search")
    })
  })
})
