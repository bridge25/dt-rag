/**
 * Get Taxonomy Tree Use Case
 *
 * Business use case for retrieving the taxonomy tree structure.
 *
 * @CODE:CLEAN-ARCHITECTURE-DOMAIN
 */

import type { TaxonomyNode, TaxonomyVersion } from '../../entities/Taxonomy';
import {
  flattenTaxonomyTree,
  getTotalDocumentCount,
} from '../../entities/Taxonomy';
import type { ITaxonomyRepository } from '../../repositories/ITaxonomyRepository';

/**
 * Use Case Response
 */
export interface GetTaxonomyTreeResult {
  tree: TaxonomyNode[];
  version: TaxonomyVersion | null;
  flatNodes: TaxonomyNode[];
  totalNodes: number;
  totalDocuments: number;
  maxDepth: number;
}

/**
 * Get Taxonomy Tree Use Case
 */
export class GetTaxonomyTreeUseCase {
  constructor(private readonly taxonomyRepository: ITaxonomyRepository) {}

  /**
   * Execute the use case
   */
  async execute(version?: string): Promise<GetTaxonomyTreeResult> {
    // Get active version if not specified
    let targetVersion = version;
    let versionInfo: TaxonomyVersion | null = null;

    if (!targetVersion) {
      versionInfo = await this.taxonomyRepository.getActiveVersion();
      targetVersion = versionInfo?.version || 'v1';
    } else {
      const versions = await this.taxonomyRepository.getVersions();
      versionInfo = versions.find((v) => v.version === targetVersion) || null;
    }

    // Get the tree
    const tree = await this.taxonomyRepository.getTree(targetVersion);

    // Compute statistics
    const flatNodes = flattenTaxonomyTree(tree);
    const totalDocuments = tree.reduce(
      (sum, node) => sum + getTotalDocumentCount(node),
      0
    );
    const maxDepth = this.calculateMaxDepth(tree);

    return {
      tree,
      version: versionInfo,
      flatNodes,
      totalNodes: flatNodes.length,
      totalDocuments,
      maxDepth,
    };
  }

  /**
   * Calculate the maximum depth of the tree
   */
  private calculateMaxDepth(nodes: TaxonomyNode[]): number {
    if (nodes.length === 0) return 0;

    let maxDepth = 0;

    function traverse(node: TaxonomyNode, depth: number) {
      maxDepth = Math.max(maxDepth, depth);
      if (node.children) {
        for (const child of node.children) {
          traverse(child, depth + 1);
        }
      }
    }

    for (const node of nodes) {
      traverse(node, 1);
    }

    return maxDepth;
  }
}

/**
 * Factory function for creating the use case
 */
export function createGetTaxonomyTreeUseCase(
  taxonomyRepository: ITaxonomyRepository
): GetTaxonomyTreeUseCase {
  return new GetTaxonomyTreeUseCase(taxonomyRepository);
}
