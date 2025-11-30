/**
 * Taxonomy Domain Entity
 *
 * Core business entity representing a Taxonomy Node in the knowledge hierarchy.
 * This entity is framework-agnostic and contains only business logic.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

/**
 * Taxonomy Node Entity - Represents a node in the taxonomy tree
 */
export interface TaxonomyNode {
  readonly id: string;
  readonly name: string;
  readonly path: readonly string[];
  readonly parentId: string | null;
  readonly level: number;
  readonly documentCount: number;
  readonly connectionCount?: number;
  readonly children?: readonly TaxonomyNode[];
  readonly metadata?: Record<string, unknown>;
}

/**
 * Taxonomy Version Entity
 */
export interface TaxonomyVersion {
  readonly version: string;
  readonly createdAt: Date;
  readonly nodeCount: number;
  readonly documentCount: number;
  readonly changes: readonly TaxonomyChange[];
  readonly isActive: boolean;
}

/**
 * Taxonomy change record
 */
export interface TaxonomyChange {
  readonly type: 'added' | 'modified' | 'removed';
  readonly nodeId: string;
  readonly nodeName: string;
  readonly timestamp: Date;
}

/**
 * Taxonomy filter parameters
 */
export interface TaxonomyFilterParams {
  version?: string;
  parentId?: string;
  minLevel?: number;
  maxLevel?: number;
  minDocuments?: number;
  searchTerm?: string;
}

/**
 * Domain logic: Get full path string from taxonomy node
 */
export function getTaxonomyPathString(node: TaxonomyNode): string {
  return node.path.join(' > ');
}

/**
 * Domain logic: Check if node is a leaf (no children)
 */
export function isTaxonomyLeaf(node: TaxonomyNode): boolean {
  return !node.children || node.children.length === 0;
}

/**
 * Domain logic: Check if node is a root (no parent)
 */
export function isTaxonomyRoot(node: TaxonomyNode): boolean {
  return node.parentId === null && node.level === 1;
}

/**
 * Domain logic: Get total document count including children
 */
export function getTotalDocumentCount(node: TaxonomyNode): number {
  let total = node.documentCount;

  if (node.children) {
    for (const child of node.children) {
      total += getTotalDocumentCount(child);
    }
  }

  return total;
}

/**
 * Domain logic: Flatten taxonomy tree to array
 */
export function flattenTaxonomyTree(nodes: readonly TaxonomyNode[]): TaxonomyNode[] {
  const result: TaxonomyNode[] = [];

  function traverse(node: TaxonomyNode) {
    result.push(node);
    if (node.children) {
      for (const child of node.children) {
        traverse(child);
      }
    }
  }

  for (const node of nodes) {
    traverse(node);
  }

  return result;
}

/**
 * Domain logic: Find node by ID in taxonomy tree
 */
export function findTaxonomyNode(
  nodes: readonly TaxonomyNode[],
  nodeId: string
): TaxonomyNode | null {
  for (const node of nodes) {
    if (node.id === nodeId) {
      return node;
    }
    if (node.children) {
      const found = findTaxonomyNode(node.children, nodeId);
      if (found) return found;
    }
  }
  return null;
}

/**
 * Domain logic: Get ancestors of a node
 */
export function getTaxonomyAncestors(
  nodes: readonly TaxonomyNode[],
  nodeId: string
): TaxonomyNode[] {
  const ancestors: TaxonomyNode[] = [];
  const node = findTaxonomyNode(nodes, nodeId);

  if (!node || !node.parentId) return ancestors;

  let currentParentId: string | null = node.parentId;

  while (currentParentId) {
    const parent = findTaxonomyNode(nodes, currentParentId);
    if (parent) {
      ancestors.unshift(parent);
      currentParentId = parent.parentId;
    } else {
      break;
    }
  }

  return ancestors;
}
