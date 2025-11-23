---
id: TAXONOMY-BUILDER-001
version: 0.0.1
status: draft
created: 2025-11-23
updated: 2025-11-23
author: "@user"
priority: high
category: frontend
labels: [taxonomy, ui, builder, drag-drop]
related_specs: [TAXONOMY-EVOLUTION-001, FRONTEND-MIGRATION-002]
---

# @SPEC:TAXONOMY-BUILDER-001: Interactive Taxonomy Builder Interface

## HISTORY

### v0.0.1 (2025-11-23)
- **INITIAL**: Initial creation of Interactive Taxonomy Builder specification
- **AUTHOR**: @user
- **SCOPE**: Frontend interface for creating, editing, and managing taxonomies
- **CONTEXT**: Dynamic Taxonomy is the core differentiator of DT-RAG. Users need intuitive tools to visualize and manipulate the taxonomy structure.

## SUMMARY (English)

This SPEC defines the Interactive Taxonomy Builder interface for DT-RAG. It enables users to visually create, edit, and manage taxonomy structures through an intuitive drag-and-drop interface. Key features include tree/graph visualization, CRUD operations for nodes/edges, real-time preview, and template support. The builder transforms the static taxonomy display into an active workspace where users can shape their knowledge organization system.

---

## Overview

The Interactive Taxonomy Builder is the primary interface for users to construct and modify their knowledge taxonomy. Unlike the read-only Taxonomy Explorer, the Builder provides full editing capabilities with an intuitive visual interface.

### Core Value Proposition
- **Visual Construction**: Build taxonomies through drag-and-drop instead of code
- **Real-time Feedback**: See taxonomy changes immediately
- **Template System**: Start from pre-built taxonomy templates
- **Validation**: Automatic cycle detection and structure validation

---

## Requirements (EARS Format)

### Ubiquitous Requirements

**UBI-001**: The system SHALL provide a visual taxonomy builder interface accessible from the main navigation.

**UBI-002**: The taxonomy builder SHALL display the current taxonomy structure as an interactive tree or graph visualization.

**UBI-003**: The system SHALL support both tree view and graph view rendering modes.

### Event-Driven Requirements

**EVT-001**: WHEN the user clicks "Add Node" button, the system SHALL display a node creation form with fields for name, description, parent selection, and metadata.

**EVT-002**: WHEN the user drags a node and drops it onto another node, the system SHALL update the parent-child relationship and re-render the visualization.

**EVT-003**: WHEN the user double-clicks on a node, the system SHALL open an inline editor for quick name/description updates.

**EVT-004**: WHEN the user right-clicks on a node, the system SHALL display a context menu with options: Edit, Delete, Add Child, Copy, Cut, Paste.

**EVT-005**: WHEN the user clicks "Save" button, the system SHALL:
- Validate the taxonomy structure (no cycles, valid relationships)
- Send the updated taxonomy to the backend API
- Display success/error notification
- Update the version history

**EVT-006**: WHEN the user clicks "Import Template" button, the system SHALL display a modal with available taxonomy templates categorized by domain (e.g., Medical, Legal, Technical).

**EVT-007**: WHEN the user selects a template, the system SHALL:
- Load the template structure
- Merge with existing taxonomy OR replace (user choice)
- Highlight newly added nodes

**EVT-008**: WHEN the user presses Ctrl+Z (or Cmd+Z on Mac), the system SHALL undo the last action.

**EVT-009**: WHEN the user presses Ctrl+Y (or Cmd+Y on Mac), the system SHALL redo the previously undone action.

### State-Driven Requirements

**STT-001**: WHILE the taxonomy has unsaved changes, the system SHALL:
- Display a visual indicator (e.g., asterisk in title)
- Show "Unsaved changes" warning on navigation attempt
- Enable auto-save every 30 seconds

**STT-002**: WHILE the user is dragging a node, the system SHALL:
- Highlight valid drop targets
- Show preview of the new structure
- Disable invalid drop zones (e.g., dropping parent into child)

**STT-003**: WHILE a node is selected, the system SHALL:
- Display node details in a side panel
- Highlight connected nodes (parents and children)
- Show associated documents count

**STT-004**: WHILE the taxonomy is being saved, the system SHALL:
- Display a loading indicator
- Disable editing operations
- Queue any additional changes

### Optional Requirements

**OPT-001**: WHERE the user has advanced permissions, the system MAY allow bulk operations (mass delete, mass move, mass re-categorize).

**OPT-002**: WHERE the taxonomy exceeds 100 nodes, the system SHOULD provide:
- Search/filter functionality
- Collapse/expand all controls
- Minimap navigation

**OPT-003**: WHERE the user prefers keyboard navigation, the system MAY support:
- Arrow keys for navigation
- Enter for edit
- Delete for removal
- Tab for next sibling

### Unwanted Behaviors

**UNW-001**: IF the user attempts to create a circular relationship (node A → B → C → A), the system SHALL:
- Prevent the operation
- Display clear error message explaining the cycle
- Highlight the conflicting path

**UNW-002**: IF the user attempts to delete a node with children, the system SHALL:
- Display confirmation dialog
- Show count of affected child nodes
- Offer options: Delete All, Move Children to Parent, Cancel

**UNW-003**: IF the backend save fails, the system SHALL:
- Preserve the local state
- Display retry option
- Log error for debugging

**UNW-004**: IF the user navigates away with unsaved changes, the system SHALL:
- Display confirmation dialog
- Offer Save, Discard, or Cancel options

---

## Technical Specifications

### Component Architecture

```typescript
// Main Builder Component
interface TaxonomyBuilderProps {
  taxonomyId: string;
  initialData?: TaxonomyNode[];
  onSave: (taxonomy: TaxonomyNode[]) => Promise<void>;
  readOnly?: boolean;
}

// Node Data Structure
interface TaxonomyNode {
  id: string;
  name: string;
  description?: string;
  parentId: string | null;
  children: string[];
  metadata: {
    documentsCount: number;
    createdAt: string;
    updatedAt: string;
    createdBy: string;
  };
  position?: { x: number; y: number }; // For graph view
}

// Builder State
interface BuilderState {
  nodes: Map<string, TaxonomyNode>;
  selectedNodeId: string | null;
  viewMode: 'tree' | 'graph';
  undoStack: TaxonomyAction[];
  redoStack: TaxonomyAction[];
  isDirty: boolean;
  isLoading: boolean;
}
```

### UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Toolbar                                                        │
│  [Add Node] [Import] [Export] [Undo] [Redo] [Save]  |  View: ○● │
├─────────────────────────────────────┬───────────────────────────┤
│                                     │                           │
│                                     │  Node Details Panel       │
│       Taxonomy Visualization        │  ─────────────────────    │
│       (Tree or Graph View)          │  Name: [__________]       │
│                                     │  Description: [_______]   │
│       ┌─ Root                       │  Parent: [Dropdown___]    │
│       ├── Category A                │  Documents: 42            │
│       │   ├── Sub A1                │  Created: 2025-01-15      │
│       │   └── Sub A2                │                           │
│       └── Category B                │  [Delete] [Add Child]     │
│           └── Sub B1                │                           │
│                                     │                           │
├─────────────────────────────────────┴───────────────────────────┤
│  Status Bar: "3 unsaved changes" | Last saved: 5 min ago        │
└─────────────────────────────────────────────────────────────────┘
```

### API Integration

```typescript
// API Endpoints
POST   /api/v1/taxonomy                    // Create taxonomy
GET    /api/v1/taxonomy/{id}              // Get taxonomy
PUT    /api/v1/taxonomy/{id}              // Update taxonomy
DELETE /api/v1/taxonomy/{id}              // Delete taxonomy
GET    /api/v1/taxonomy/{id}/nodes        // Get all nodes
POST   /api/v1/taxonomy/{id}/nodes        // Add node
PUT    /api/v1/taxonomy/{id}/nodes/{nodeId}  // Update node
DELETE /api/v1/taxonomy/{id}/nodes/{nodeId}  // Delete node
GET    /api/v1/taxonomy/templates         // List templates
POST   /api/v1/taxonomy/{id}/import       // Import template
```

### Technology Stack

- **Visualization**: D3.js for graph view, react-arborist for tree view
- **State Management**: Zustand with immer for immutable updates
- **Drag & Drop**: @dnd-kit/core for accessible drag-and-drop
- **Data Fetching**: TanStack Query v5 for server state
- **UI Components**: shadcn/ui + Tailwind CSS

---

## Acceptance Criteria

### AC-001: Basic Node Operations
**Given** the taxonomy builder is open with an existing taxonomy
**When** the user clicks "Add Node" and fills in the form
**Then** a new node appears in the visualization at the correct position

### AC-002: Drag and Drop Reparenting
**Given** the taxonomy has nodes A and B at the same level
**When** the user drags node B onto node A
**Then** node B becomes a child of node A and the tree re-renders

### AC-003: Undo/Redo Functionality
**Given** the user has performed 3 operations (add, move, rename)
**When** the user presses Ctrl+Z three times
**Then** all operations are undone in reverse order

### AC-004: Template Import
**Given** the user has an empty taxonomy
**When** the user imports the "Medical" template
**Then** the taxonomy is populated with the medical taxonomy structure

### AC-005: Cycle Prevention
**Given** nodes exist in hierarchy: Root → A → B → C
**When** the user attempts to drag Root onto C
**Then** the system prevents the operation and shows an error

---

## Implementation Priority

1. **Phase 1**: Basic tree visualization with add/edit/delete
2. **Phase 2**: Drag-and-drop reparenting
3. **Phase 3**: Undo/redo and auto-save
4. **Phase 4**: Template system
5. **Phase 5**: Graph view mode

---

## Traceability (@TAG)

- **SPEC**: @SPEC:TAXONOMY-BUILDER-001
- **TEST**: tests/frontend/taxonomy-builder/
- **CODE**: apps/frontend/components/taxonomy-builder/
- **DOC**: docs/features/taxonomy-builder.md
