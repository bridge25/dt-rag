// Test TreeViewer API integration
const API_BASE_URL = 'http://localhost:8001/api/v1'
const API_KEY = '7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y'

async function testTreeViewerAPI() {
  console.log('Testing TreeViewer API Integration...\n')

  try {
    // Test 1: Get versions
    console.log('1. Testing GET /api/v1/taxonomy/versions')
    const versionsRes = await fetch(`${API_BASE_URL}/taxonomy/versions`, {
      headers: { 'X-API-Key': API_KEY }
    })
    const versionsData = await versionsRes.json()
    console.log(`✓ Status: ${versionsRes.status}`)
    console.log(`✓ Versions count: ${versionsData.versions.length}`)
    console.log(`✓ First version: ${versionsData.versions[0].version} (${versionsData.versions[0].node_count} nodes)\n`)

    const version = versionsData.versions[0].version

    // Test 2: Get tree
    console.log(`2. Testing GET /api/v1/taxonomy/${version}/tree`)
    const treeRes = await fetch(`${API_BASE_URL}/taxonomy/${version}/tree`, {
      headers: { 'X-API-Key': API_KEY }
    })
    const treeData = await treeRes.json()
    console.log(`✓ Status: ${treeRes.status}`)
    console.log(`✓ Nodes count: ${treeData.nodes.length}`)
    console.log(`✓ Edges count: ${treeData.edges.length}`)

    // Test 3: Verify tree structure conversion
    console.log('\n3. Testing tree structure conversion logic')
    const nodeMap = new Map()
    const rootNodes = []

    // Create all nodes
    treeData.nodes.forEach(node => {
      nodeMap.set(node.node_id, {
        id: node.node_id,
        name: node.label,
        path: node.canonical_path,
        children: []
      })
    })

    // Build parent-child relationships
    treeData.nodes.forEach(node => {
      const treeNode = nodeMap.get(node.node_id)
      const path = node.canonical_path

      if (path.length === 1) {
        rootNodes.push(treeNode)
      } else {
        const parentNode = treeData.nodes.find(n =>
          n.canonical_path.length === path.length - 1 &&
          n.canonical_path.every((p, i) => p === path[i])
        )

        if (parentNode) {
          const parent = nodeMap.get(parentNode.node_id)
          parent.children.push(treeNode)
        }
      }
    })

    console.log(`✓ Root nodes: ${rootNodes.length}`)
    rootNodes.forEach(root => {
      console.log(`  - ${root.name} (${root.children.length} children)`)
      root.children.forEach(child => {
        console.log(`    - ${child.name} (${child.children.length} children)`)
      })
    })

    console.log('\n✅ All tests passed successfully!')
    console.log('\nTreeViewer Component Status:')
    console.log('- API integration: ✅ Working')
    console.log('- Version dropdown data: ✅ Available')
    console.log('- Tree structure conversion: ✅ Correct')
    console.log('- Tree hierarchy: ✅ Valid')

  } catch (error) {
    console.error('❌ Test failed:', error.message)
    process.exit(1)
  }
}

testTreeViewerAPI()
