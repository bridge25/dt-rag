'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bookmark,
  Plus,
  Search,
  X,
  Edit3,
  Trash2,
  Clock,
  User,
  Globe,
  Lock
} from 'lucide-react'
import { SavedSearch } from '@/types/search'
import { Button, Input, Label } from '@/components/ui'
import { formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface SavedSearchesProps {
  savedSearches: SavedSearch[]
  onSearchSelect: (search: SavedSearch) => void
  onClose: () => void
}

export function SavedSearches({
  savedSearches,
  onSearchSelect,
  onClose
}: SavedSearchesProps) {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingSearch, setEditingSearch] = useState<string | null>(null)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="border rounded-lg bg-background p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Bookmark className="h-5 w-5" />
          <h3 className="text-lg font-medium">Saved Searches</h3>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCreateForm(true)}
          >
            <Plus className="h-4 w-4 mr-1" />
            New
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {showCreateForm && (
          <CreateSearchForm
            onSave={(search) => {
              // TODO: Implement save functionality
              console.log('Saving search:', search)
              setShowCreateForm(false)
            }}
            onCancel={() => setShowCreateForm(false)}
          />
        )}
      </AnimatePresence>

      {/* Saved Searches List */}
      <div className="space-y-3">
        {savedSearches.length === 0 ? (
          <div className="text-center py-8">
            <Bookmark className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
            <p className="text-sm text-muted-foreground">No saved searches yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              Save your frequent searches for quick access
            </p>
          </div>
        ) : (
          savedSearches.map((search) => (
            <SavedSearchItem
              key={search.id}
              search={search}
              isEditing={editingSearch === search.id}
              onSelect={() => onSearchSelect(search)}
              onEdit={() => setEditingSearch(search.id)}
              onCancelEdit={() => setEditingSearch(null)}
              onSaveEdit={(updatedSearch) => {
                // TODO: Implement update functionality
                console.log('Updating search:', updatedSearch)
                setEditingSearch(null)
              }}
              onDelete={() => {
                // TODO: Implement delete functionality
                console.log('Deleting search:', search.id)
              }}
            />
          ))
        )}
      </div>
    </motion.div>
  )
}

interface CreateSearchFormProps {
  onSave: (search: Omit<SavedSearch, 'id' | 'created_at' | 'created_by'>) => void
  onCancel: () => void
}

function CreateSearchForm({ onSave, onCancel }: CreateSearchFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (name.trim()) {
      onSave({
        name: name.trim(),
        query: '', // TODO: Get current query from store
        filters: {}, // TODO: Get current filters from store
        description: description.trim() || undefined,
        is_public: isPublic
      })
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="border rounded-lg p-4 mb-4 bg-accent/30"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="search-name">Name</Label>
          <Input
            id="search-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter search name..."
            autoFocus
          />
        </div>

        <div>
          <Label htmlFor="search-description">Description (optional)</Label>
          <Input
            id="search-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe this search..."
          />
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="search-public"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="rounded"
          />
          <Label htmlFor="search-public" className="text-sm">
            Make this search public
          </Label>
        </div>

        <div className="flex justify-end space-x-2">
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" size="sm" disabled={!name.trim()}>
            Save Search
          </Button>
        </div>
      </form>
    </motion.div>
  )
}

interface SavedSearchItemProps {
  search: SavedSearch
  isEditing: boolean
  onSelect: () => void
  onEdit: () => void
  onCancelEdit: () => void
  onSaveEdit: (search: SavedSearch) => void
  onDelete: () => void
}

function SavedSearchItem({
  search,
  isEditing,
  onSelect,
  onEdit,
  onCancelEdit,
  onSaveEdit,
  onDelete
}: SavedSearchItemProps) {
  const [editName, setEditName] = useState(search.name)
  const [editDescription, setEditDescription] = useState(search.description || '')

  const handleSaveEdit = () => {
    onSaveEdit({
      ...search,
      name: editName.trim(),
      description: editDescription.trim() || undefined
    })
  }

  if (isEditing) {
    return (
      <motion.div
        layout
        className="border rounded-lg p-4 bg-accent/30"
      >
        <div className="space-y-3">
          <Input
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="Search name..."
          />
          <Input
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Description..."
          />
          <div className="flex justify-end space-x-2">
            <Button variant="ghost" size="sm" onClick={onCancelEdit}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSaveEdit} disabled={!editName.trim()}>
              Save
            </Button>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      layout
      className={cn(
        "border rounded-lg p-4 cursor-pointer transition-colors",
        "hover:bg-accent/50"
      )}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h4 className="font-medium text-sm truncate">{search.name}</h4>
            <div className="flex items-center space-x-1">
              {search.is_public ? (
                <Globe className="h-3 w-3 text-muted-foreground" />
              ) : (
                <Lock className="h-3 w-3 text-muted-foreground" />
              )}
            </div>
          </div>

          {search.description && (
            <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
              {search.description}
            </p>
          )}

          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            <Search className="h-3 w-3" />
            <span className="truncate max-w-32">{search.query}</span>
          </div>

          <div className="flex items-center space-x-4 mt-2 text-xs text-muted-foreground">
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{formatRelativeTime(search.created_at)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <User className="h-3 w-3" />
              <span>{search.created_by}</span>
            </div>
            {Object.keys(search.filters).length > 0 && (
              <span>{Object.keys(search.filters).length} filter(s)</span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-1 ml-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit()
            }}
            className="p-1 hover:bg-accent rounded opacity-0 group-hover:opacity-100"
            title="Edit search"
          >
            <Edit3 className="h-3 w-3" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
            className="p-1 hover:bg-accent rounded text-destructive opacity-0 group-hover:opacity-100"
            title="Delete search"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>
    </motion.div>
  )
}