import { z } from "zod"

const SourceMetaSchema = z.object({
  url: z.string(),
  title: z.string(),
  date: z.string(),
  author: z.string().nullish(),
  content_type: z.string().nullish(),
  language: z.string().nullish(),
})

const SearchHitSchema = z.object({
  chunk_id: z.string(),
  score: z.number(),
  text: z.string(),
  source: SourceMetaSchema,
  taxonomy_path: z.array(z.string()),
  highlights: z.array(z.string()).nullish(),
  metadata: z.record(z.string(), z.any()).nullish(),
})

const SearchResponseSchema = z.object({
  hits: z.array(SearchHitSchema),
  latency: z.number(),
  request_id: z.string(),
  total_candidates: z.number().optional(),
  sources_count: z.number().optional(),
  taxonomy_version: z.string().optional(),
  query_analysis: z.record(z.string(), z.any()).nullish(),
})

async function testValidation() {
  try {
    const response = await fetch("http://localhost:8000/api/v1/search/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"
      },
      body: JSON.stringify({
        q: "machine learning",
        max_results: 3
      })
    })

    if (!response.ok) {
      console.error(`❌ API Error: ${response.status} ${response.statusText}`)
      process.exit(1)
    }

    const data = await response.json()
    console.log("✅ API Response received")
    console.log(`   Hits: ${data.hits?.length || 0}`)

    const parsed = SearchResponseSchema.parse(data)
    console.log("✅ Zod Validation PASSED")
    console.log(`   - ${parsed.hits.length} hits validated successfully`)
    console.log(`   - Latency: ${parsed.latency}ms`)
    console.log(`   - Request ID: ${parsed.request_id}`)

    if (parsed.hits.length > 0) {
      const firstHit = parsed.hits[0]
      console.log("\n📋 Sample Hit Validation:")
      console.log(`   - author: ${firstHit.source.author === null ? "null (OK)" : firstHit.source.author}`)
      console.log(`   - content_type: ${firstHit.source.content_type === null ? "null (OK)" : firstHit.source.content_type}`)
      console.log(`   - language: ${firstHit.source.language === null ? "null (OK)" : firstHit.source.language}`)
      console.log(`   - highlights: ${firstHit.highlights === null ? "null (OK)" : "array"}`)
      console.log(`   - metadata: ${firstHit.metadata === null ? "null (OK)" : "object"}`)
    }

    process.exit(0)
  } catch (error) {
    if (error.name === "ZodError") {
      console.error("❌ Zod Validation FAILED:")
      console.error(JSON.stringify(error.errors, null, 2))
    } else {
      console.error("❌ Test Error:", error.message)
    }
    process.exit(1)
  }
}

testValidation()
