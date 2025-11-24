# Acceptance Criteria: SPEC-TAXONOMY-BUILDER-001

## Test Scenarios

### Scenario 1: Create New Node
**Given** the taxonomy builder is loaded with an existing taxonomy
**When** the user clicks "Add Node" button
**And** fills in name: "Machine Learning" and description: "ML techniques"
**And** selects parent: "Artificial Intelligence"
**And** clicks "Save"
**Then** the new node appears under "Artificial Intelligence"
**And** the tree view updates automatically
**And** a success notification is displayed

### Scenario 2: Drag-Drop Reparenting
**Given** taxonomy has structure: AI → ML, AI → Deep Learning
**When** the user drags "Deep Learning" onto "ML"
**Then** "Deep Learning" becomes a child of "ML"
**And** the path shows: AI → ML → Deep Learning
**And** the change is marked as unsaved

### Scenario 3: Prevent Circular Reference
**Given** taxonomy has: A → B → C
**When** the user attempts to drag "A" onto "C"
**Then** the drop is rejected
**And** error message shows: "Cannot create circular reference"
**And** the invalid path is highlighted in red

### Scenario 4: Undo Operation
**Given** the user has added a new node "Test"
**When** the user presses Ctrl+Z
**Then** the "Test" node is removed
**And** the undo stack shows 0 items
**And** the redo stack shows 1 item

### Scenario 5: Auto-Save
**Given** the user has made changes 30 seconds ago
**When** the auto-save timer triggers
**Then** changes are saved to the backend
**And** status bar shows "Last saved: just now"
**And** the dirty flag is cleared

### Scenario 6: Template Import
**Given** an empty taxonomy
**When** the user clicks "Import Template"
**And** selects "Medical Taxonomy" template
**Then** the taxonomy is populated with medical categories
**And** all nodes are highlighted as "new"
**And** the import count shows "42 nodes imported"

### Scenario 7: Delete Node with Children
**Given** node "Parent" has 3 children
**When** the user right-clicks "Parent" and selects "Delete"
**Then** confirmation dialog appears
**And** shows "This will delete 3 child nodes"
**And** offers options: [Delete All] [Move to Grandparent] [Cancel]

### Scenario 8: Unsaved Changes Warning
**Given** the taxonomy has unsaved changes
**When** the user clicks browser back button
**Then** confirmation dialog appears
**And** shows "You have unsaved changes"
**And** offers options: [Save] [Discard] [Stay]

## Performance Requirements
- Tree with 500 nodes renders in < 1 second
- Drag preview updates at 60fps
- Save operation completes in < 2 seconds

## Accessibility Requirements
- All actions accessible via keyboard
- ARIA labels for screen readers
- Color contrast ratio ≥ 4.5:1
