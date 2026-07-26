import { useState, type ReactNode } from 'react'
import { useUIStore, type SidebarView } from '../stores/uiStore'
import { useChatStore, type ConversationSession, type ConversationFolder } from '../stores/chatStore'

type NavItem = {
  view: SidebarView
  label: string
  icon: ReactNode
}

const navItems: NavItem[] = [
  {
    view: 'history',
    label: 'Conversations',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  },
  {
    view: 'pinned',
    label: 'Pinned',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l3 6 6 .5-4.5 4.5L18 21l-6-3-6 3 1.5-7L3 9.5 9 9z"/></svg>,
  },
  {
    view: 'cases',
    label: 'Recent Cases',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h7l2 2h9v10H3z"/></svg>,
  },
  {
    view: 'bookmarks',
    label: 'Bookmarks',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>,
  },
  {
    view: 'saved-searches',
    label: 'Saved Searches',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.3-4.3"/></svg>,
  },
  {
    view: 'tags',
    label: 'Tags',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>,
  },
  {
    view: 'archived',
    label: 'Archived',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>,
  },
  {
    view: 'folders',
    label: 'Folders',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h7l2 2h9v10H3z"/></svg>,
  },
]

function SessionItem({ session, onSelect, onRename, onArchive, onPin }: {
  session: ConversationSession
  onSelect: () => void
  onRename: (title: string) => void
  onArchive: () => void
  onPin: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(session.title)
  const currentId = useChatStore((s) => s.currentSessionId)

  return (
    <div className={`group relative rounded-lg border p-2.5 text-xs transition-colors ${
      currentId === session.id
        ? 'border-teal-200 bg-teal-50/50'
        : 'border-transparent hover:border-slate-100 hover:bg-slate-50'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <button type="button" onClick={onSelect} className="min-w-0 flex-1 text-left">
          {editing ? (
            <input
              autoFocus
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onBlur={() => { onRename(editTitle); setEditing(false) }}
              onKeyDown={(e) => { if (e.key === 'Enter') { onRename(editTitle); setEditing(false) } if (e.key === 'Escape') setEditing(false) }}
              className="w-full rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs outline-none"
            />
          ) : (
            <span className="font-medium text-slate-800 line-clamp-1">{session.title}</span>
          )}
          <span className="mt-0.5 block text-[10px] text-slate-400">
            {session.messageCount} messages · {new Date(session.updatedAt).toLocaleDateString()}
          </span>
        </button>
        <div className="flex shrink-0 gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button type="button" onClick={() => setEditing(true)} className="flex h-6 w-6 items-center justify-center rounded text-slate-400 hover:bg-slate-100 hover:text-slate-700" title="Rename">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button type="button" onClick={onPin} className={`flex h-6 w-6 items-center justify-center rounded ${session.pinned ? 'text-amber-500' : 'text-slate-400 hover:text-slate-700'}`} title={session.pinned ? 'Unpin' : 'Pin'}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill={session.pinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2"><path d="M12 3l3 6 6 .5-4.5 4.5L18 21l-6-3-6 3 1.5-7L3 9.5 9 9z"/></svg>
          </button>
          <button type="button" onClick={onArchive} className="flex h-6 w-6 items-center justify-center rounded text-slate-400 hover:bg-slate-100 hover:text-slate-700" title="Archive">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>
          </button>
        </div>
      </div>
      {session.tags.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {session.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[9px] text-slate-600">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function HistoryPanel() {
  const { sessions, currentSessionId, restoreSession, renameSession, archiveSession, pinSession, removeSession, sessionSearch, setSessionSearch } = useChatStore()
  const [showArchived, setShowArchived] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [searchTag, setSearchTag] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  let filtered = sessions.filter((s) => {
    if (!showArchived && s.archived) return false
    if (sessionSearch && !s.title.toLowerCase().includes(sessionSearch.toLowerCase())) return false
    if (searchTag && !s.tags.some((t) => t.toLowerCase().includes(searchTag.toLowerCase()))) return false
    if (dateFrom && s.updatedAt < new Date(dateFrom).getTime()) return false
    if (dateTo && s.updatedAt > new Date(dateTo + 'T23:59:59').getTime()) return false
    return true
  })

  filtered = [...filtered].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1
    if (!a.pinned && b.pinned) return 1
    return b.updatedAt - a.updatedAt
  })

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-100 p-3">
        <div className="relative">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.3-4.3"/></svg>
          <input
            value={sessionSearch}
            onChange={(e) => setSessionSearch(e.target.value)}
            placeholder="Search conversations..."
            className="w-full rounded-lg border border-slate-200 bg-white py-1.5 pl-8 pr-8 text-xs outline-none placeholder:text-slate-400 focus:border-teal-300"
            aria-label="Search conversations"
          />
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 ${showFilters ? 'text-teal-600' : 'text-slate-400 hover:text-slate-600'}`}
            aria-label="Toggle search filters"
            aria-expanded={showFilters}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" y1="6" x2="20" y2="6"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="12" y1="18" x2="12" y2="18"/></svg>
          </button>
        </div>
        {showFilters && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            <input
              value={searchTag}
              onChange={(e) => setSearchTag(e.target.value)}
              placeholder="Filter by tag..."
              className="flex-1 rounded border border-slate-200 bg-white px-2 py-1 text-[10px] outline-none placeholder:text-slate-400 focus:border-teal-300"
              aria-label="Filter by tag"
            />
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-[120px] rounded border border-slate-200 bg-white px-2 py-1 text-[10px] outline-none focus:border-teal-300"
              aria-label="From date"
            />
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-[120px] rounded border border-slate-200 bg-white px-2 py-1 text-[10px] outline-none focus:border-teal-300"
              aria-label="To date"
            />
          </div>
        )}
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto p-3">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <p className="text-sm font-medium text-slate-600">
              {sessionSearch || searchTag || dateFrom || dateTo ? 'No matching conversations' : 'No conversations yet'}
            </p>
            <p className="mt-1 text-xs text-slate-400">
              {(sessionSearch || searchTag || dateFrom || dateTo) ? 'Try different search terms or filters.' : 'Start a new chat to see it here.'}
            </p>
          </div>
        ) : (
          filtered.map((session) => (
            <SessionItem
              key={session.id}
              session={session}
              onSelect={() => restoreSession(session.id)}
              onRename={(title) => renameSession(session.id, title)}
              onArchive={() => archiveSession(session.id)}
              onPin={() => pinSession(session.id)}
            />
          ))
        )}
      </div>
      <div className="border-t border-slate-100 p-2">
        <button
          type="button"
          onClick={() => setShowArchived(!showArchived)}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs text-slate-500 hover:bg-slate-50 hover:text-slate-700"
          aria-label={showArchived ? 'Hide archived conversations' : `Show archived conversations (${sessions.filter(s => s.archived).length})`}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>
          {showArchived ? 'Hide archived' : `Show archived (${sessions.filter(s => s.archived).length})`}
        </button>
      </div>
    </div>
  )
}

function PinnedPanel() {
  const { sessions, restoreSession, renameSession, pinSession, archiveSession } = useChatStore()
  const pinned = sessions.filter((s) => s.pinned)

  if (pinned.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 3l3 6 6 .5-4.5 4.5L18 21l-6-3-6 3 1.5-7L3 9.5 9 9z"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No pinned conversations</p>
        <p className="mt-1 text-xs text-slate-400">Pin conversations to access them quickly.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1 p-3">
      {pinned.map((session) => (
        <SessionItem
          key={session.id}
          session={session}
          onSelect={() => restoreSession(session.id)}
          onRename={(title) => renameSession(session.id, title)}
          onArchive={() => archiveSession(session.id)}
          onPin={() => pinSession(session.id)}
        />
      ))}
    </div>
  )
}

function BookmarksPanel() {
  const { messages, toggleBookmark } = useChatStore()
  const bookmarked = messages.filter((m) => m.bookmarked)

  if (bookmarked.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No bookmarks</p>
        <p className="mt-1 text-xs text-slate-400">Bookmark important messages to find them later.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1 p-3">
      {bookmarked.map((m) => (
        <div key={m.id} className="rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
          <div className="flex items-start justify-between gap-2">
            <span className="font-medium text-slate-800 line-clamp-2">{m.text || m.kind}</span>
            <button type="button" onClick={() => toggleBookmark(m.id)} className="shrink-0 text-amber-500 hover:text-amber-600">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
            </button>
          </div>
          <span className="mt-1 block text-[10px] text-slate-400">
            {m.timestamp ? new Date(m.timestamp).toLocaleString() : ''}
          </span>
        </div>
      ))}
    </div>
  )
}

function TagsPanel() {
  const { messages, addTag, removeTag } = useChatStore()
  const allTags = new Set<string>()
  messages.forEach((m) => {
    const tags = (m as any).tags || []
    tags.forEach((t: string) => allTags.add(t))
  })
  const tagList = Array.from(allTags)

  if (tagList.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No tags</p>
        <p className="mt-1 text-xs text-slate-400">Tag messages to organize your investigation.</p>
      </div>
    )
  }

  return (
    <div className="space-y-2 p-3">
      {tagList.map((tag) => {
        const count = messages.filter((m) => ((m as any).tags || []).includes(tag)).length
        return (
          <div key={tag} className="flex items-center justify-between rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
            <span className="font-medium text-slate-700">{tag}</span>
            <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">{count}</span>
          </div>
        )
      })}
    </div>
  )
}

function CasesPanel() {
  const { sessions } = useChatStore()
  const recent = sessions.filter((s) => s.caseId).slice(0, 10)

  if (recent.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 6h7l2 2h9v10H3z"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No recent cases</p>
        <p className="mt-1 text-xs text-slate-400">Open a case to see it here.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1 p-3">
      {recent.map((s) => (
        <div key={s.id} className="rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
          <p className="font-medium text-slate-800">{s.title}</p>
          <p className="mt-0.5 text-slate-500">{s.caseId}</p>
          <span className="mt-1 inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
            {s.messageCount} messages
          </span>
        </div>
      ))}
    </div>
  )
}

function SavedSearchesPanel() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.3-4.3"/></svg>
      </div>
      <p className="text-sm font-medium text-slate-600">Saved Searches</p>
      <p className="mt-1 text-xs text-slate-400">Save frequent searches for quick access.</p>
    </div>
  )
}

function FoldersPanel() {
  const { folders, sessions, restoreSession, renameSession, archiveSession, pinSession, createFolder, renameFolder, deleteFolder, moveSessionToFolder } = useChatStore()
  const [newFolderName, setNewFolderName] = useState('')
  const [editingFolderId, setEditingFolderId] = useState<string | null>(null)
  const [editFolderName, setEditFolderName] = useState('')

  const handleCreate = () => {
    const name = newFolderName.trim()
    if (name) {
      createFolder(name)
      setNewFolderName('')
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-100 p-3">
        <div className="flex items-center gap-1">
          <input
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleCreate() }}
            placeholder="New folder name..."
            className="flex-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs outline-none placeholder:text-slate-400 focus:border-teal-300"
          />
          <button
            type="button"
            onClick={handleCreate}
            disabled={!newFolderName.trim()}
            className="rounded-lg bg-navy-900 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {folders.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 6h7l2 2h9v10H3z"/></svg>
            </div>
            <p className="text-sm font-medium text-slate-600">No folders</p>
            <p className="mt-1 text-xs text-slate-400">Create folders to organise your conversations.</p>
          </div>
        )}
        {folders.map((folder) => {
          const folderSessions = sessions.filter((s) => s.folderId === folder.id)
          return (
            <div key={folder.id} className="rounded-lg border border-slate-100 bg-white">
              <div className="flex items-center justify-between border-b border-slate-50 px-3 py-2">
                {editingFolderId === folder.id ? (
                  <input
                    autoFocus
                    value={editFolderName}
                    onChange={(e) => setEditFolderName(e.target.value)}
                    onBlur={() => { renameFolder(folder.id, editFolderName); setEditingFolderId(null) }}
                    onKeyDown={(e) => { if (e.key === 'Enter') { renameFolder(folder.id, editFolderName); setEditingFolderId(null) } if (e.key === 'Escape') setEditingFolderId(null) }}
                    className="flex-1 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs outline-none"
                  />
                ) : (
                  <span className="text-xs font-semibold text-slate-700">{folder.name}</span>
                )}
                <div className="flex items-center gap-0.5">
                  <span className="text-[10px] text-slate-400">{folderSessions.length}</span>
                  <button type="button" onClick={() => { setEditingFolderId(folder.id); setEditFolderName(folder.name) }} className="flex h-5 w-5 items-center justify-center rounded text-slate-400 hover:bg-slate-100 hover:text-slate-700" title="Rename folder">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                  </button>
                  <button type="button" onClick={() => deleteFolder(folder.id)} className="flex h-5 w-5 items-center justify-center rounded text-slate-400 hover:bg-red-50 hover:text-red-600" title="Delete folder">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                  </button>
                </div>
              </div>
              {folderSessions.length > 0 && (
                <div className="space-y-0.5 p-2">
                  {folderSessions.map((s) => (
                    <div key={s.id} className="flex items-center justify-between rounded-md bg-slate-50 px-2 py-1.5 text-xs">
                      <button
                        type="button"
                        onClick={() => restoreSession(s.id)}
                        className="min-w-0 flex-1 text-left font-medium text-slate-700 hover:text-teal-700 line-clamp-1"
                      >
                        {s.title}
                      </button>
                      <button
                        type="button"
                        onClick={() => moveSessionToFolder(s.id, null)}
                        className="ml-1 shrink-0 text-slate-400 hover:text-red-500"
                        title="Remove from folder"
                      >
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ArchivedPanel() {
  const { sessions, restoreSession, archiveSession } = useChatStore()
  const archived = sessions.filter((s) => s.archived)

  if (archived.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No archived conversations</p>
        <p className="mt-1 text-xs text-slate-400">Archive conversations to declutter.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1 p-3">
      {archived.map((session) => (
        <SessionItem
          key={session.id}
          session={session}
          onSelect={() => restoreSession(session.id)}
          onRename={(title) => {}}
          onArchive={() => archiveSession(session.id)}
          onPin={() => {}}
        />
      ))}
    </div>
  )
}

const PANELS: Record<string, () => JSX.Element> = {
  history: HistoryPanel,
  pinned: PinnedPanel,
  cases: CasesPanel,
  bookmarks: BookmarksPanel,
  'saved-searches': SavedSearchesPanel,
  tags: TagsPanel,
  archived: ArchivedPanel,
  folders: FoldersPanel,
}

export function ConversationSidebar() {
  const { sidebarOpen, sidebarView, setSidebarView } = useUIStore()

  if (!sidebarOpen) return null

  const Panel = PANELS[sidebarView] || HistoryPanel

  return (
    <aside className="flex h-full w-72 shrink-0 border-r border-slate-200 bg-white">
      <nav className="flex w-12 shrink-0 flex-col items-center gap-1 border-r border-slate-100 bg-slate-50 py-3">
        {navItems.map((item) => {
          const active = sidebarView === item.view
          return (
            <button
              key={item.view}
              type="button"
              onClick={() => setSidebarView(item.view)}
              className={`flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
                active
                  ? 'bg-navy-900 text-white'
                  : 'text-slate-400 hover:bg-slate-100 hover:text-slate-700'
              }`}
              aria-label={item.label}
              title={item.label}
            >
              {item.icon}
            </button>
          )
        })}
      </nav>
      <div className="min-w-0 flex-1 overflow-y-auto">
        <Panel />
      </div>
    </aside>
  )
}
