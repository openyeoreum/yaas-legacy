<script>
  import { onMount, tick } from 'svelte'
  import {
    BadgeCheck,
    ChevronDown,
    ChevronRight,
    FilePenLine,
    FolderOpen,
    LockKeyhole,
    Mic2,
    Music2,
    PanelLeftClose,
    PanelLeftOpen,
    Pause,
    Play,
    RefreshCw,
    Rocket,
    Search,
    Settings2,
    Terminal,
    Volume2,
  } from '@lucide/svelte'

  const API_BASE = import.meta.env.VITE_API_BASE || (window.location.port === '15174' ? 'http://127.0.0.1:18000' : 'http://127.0.0.1:8000')
  const SELECTED_PROJECT_KEY = 'yaas-audiobook-selected-project'
  const LOGO_CANDIDATES = ['/yeoreum/brand/stidio-logo.png', '/yeoreum/brand/stidio-logo.svg']
  const speeds = [1, 1.25, 1.5, 1.75, 2]

  let projects = []
  let storageRoot = ''
  let selected = null
  let state = null
  let editPayload = { data: [] }
  let voicesPayload = { data: [] }
  let musicsPayload = { data: [] }
  let configPayload = { data: {} }
  let inspectionItems = []
  let voiceAssets = []
  let musicAssets = []

  let activePanel = 'Edit'
  let search = ''
  let sidebarOpen = true
  let projectsOpen = true
  let logsOpen = false
  let selectedChunkId = null
  let nowMs = Date.now()

  let logLines = []
  let eventSource = null
  let loading = false
  let saving = false
  let runStarting = false
  let stopping = false
  let statusText = '대기 중'
  let editDirty = false
  let voiceDirty = false
  let musicDirty = false
  let configDirty = false

  let audioEl
  let currentTrack = null
  let playlist = []
  let playbackRate = 1
  let volume = 1
  let currentTime = 0
  let duration = 0
  let isPlaying = false
  let pendingSeek = null

  let logoIndex = 0
  let logoMissing = false

  $: locked = Boolean(state?.lock?.running)
  $: generationBusy = locked || runStarting || stopping
  $: projectBase = projectApiBase(selected)
  $: logoSrc = LOGO_CANDIDATES[logoIndex] || ''
  $: masterFiles = state?.audio?.master || []
  $: chunkRows = buildChunkRows(editPayload.data || [], inspectionItems)
  $: filteredChunks = chunkRows.filter((chunk) => matchesChunkSearch(chunk, search))
  $: if (!selectedChunkId && filteredChunks.length) selectedChunkId = filteredChunks[0].id
  $: if (selectedChunkId && filteredChunks.length && !filteredChunks.some((chunk) => chunk.id === selectedChunkId)) selectedChunkId = filteredChunks[0].id
  $: if (selectedChunkId && !filteredChunks.length && search.trim()) selectedChunkId = null
  $: selectedChunk = chunkRows.find((chunk) => chunk.id === selectedChunkId) || null
  $: currentAudioSrc = selected && currentTrack?.path ? api(`${projectBase}/audio?path=${encodeURIComponent(currentTrack.path)}`) : ''
  $: modifiedCount = chunkRows.filter((chunk) => chunk.modified).length
  $: masterCount = masterFiles.length
  $: jobProgress = buildJobProgress(state?.lock, logLines, state?.counts?.edits || 0, generationBusy, nowMs)
  $: topbarStatusText = shouldShowTopbarStatus(statusText) ? statusText : ''
  $: activeSave = activeSaveState(activePanel)
  $: activeSaveTitle = activeSave.path
    ? `${activeSave.label}${activeSave.dirty ? '' : ' · 저장할 변경 없음'} · ${activeSave.path}`
    : `${activeSave.label}${activeSave.dirty ? '' : ' · 저장할 변경 없음'}`

  function api(path) {
    return `${API_BASE}${path}`
  }

  function shouldShowTopbarStatus(value) {
    return Boolean(value && !['준비 완료', '대기 중'].includes(value))
  }

  function activeSaveState(panel) {
    if (panel === 'Voice') {
      return {
        label: 'Voice 저장',
        path: voicesPayload.path,
        dirty: voiceDirty,
        action: saveVoices,
      }
    }
    if (panel === 'Music') {
      return {
        label: 'Music 저장',
        path: musicsPayload.path,
        dirty: musicDirty,
        action: saveMusics,
      }
    }
    if (panel === 'Config') {
      return {
        label: 'Config 저장',
        path: configPayload.path || state?.paths?.config,
        dirty: configDirty,
        action: saveConfig,
      }
    }
    return {
      label: 'Edit 저장',
      path: editPayload.path,
      dirty: editDirty,
      action: saveEdit,
    }
  }

  function projectApiBase(project = selected) {
    return project ? `/api/audiobook/${encodeURIComponent(project.email)}/${encodeURIComponent(project.project)}` : ''
  }

  function savedProjectSelection() {
    try {
      return JSON.parse(localStorage.getItem(SELECTED_PROJECT_KEY) || 'null')
    } catch {
      return null
    }
  }

  async function request(path, options = {}) {
    const response = await fetch(api(path), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    })
    const text = await response.text()
    const payload = text ? JSON.parse(text) : {}
    if (!response.ok) {
      throw new Error(payload.detail || response.statusText)
    }
    return payload
  }

  function chunkKey(chunk) {
    return Object.prototype.hasOwnProperty.call(chunk || {}, 'ModifiedChunk') ? 'ModifiedChunk' : 'Chunk'
  }

  function chunkText(chunk) {
    return chunk?.[chunkKey(chunk)] || ''
  }

  function setChunkText(chunk, value) {
    chunk[chunkKey(chunk)] = value
    editDirty = true
    editPayload = editPayload
  }

  function cleanChunk(value) {
    const text = String(value || '').trim()
    return text.startsWith('[') && text.endsWith(']') ? text.slice(1, -1).trim() : text
  }

  function endSecond(chunk) {
    const second = Number(chunk?.EndTime?.Second)
    return Number.isFinite(second) ? second : null
  }

  function buildChunkRows(edits, inspection) {
    const audioMap = new Map((inspection || []).map((item) => [item.id, item]))
    const rows = []
    let previousEnd = 0

    for (let editIndex = 0; editIndex < (edits || []).length; editIndex += 1) {
      const edit = edits[editIndex]
      const chunks = Array.isArray(edit.ActorChunk) ? edit.ActorChunk : []
      chunks.forEach((chunk, chunkIndex) => {
        const inspectionId = `${edit.EditId}:${chunkIndex}`
        const id = `${editIndex}:${inspectionId}`
        const end = endSecond(chunk)
        const inspectionItem = audioMap.get(inspectionId)
        rows.push({
          id,
          inspectionId,
          editIndex,
          edit,
          chunk,
          editId: edit.EditId,
          chunkIndex,
          tag: edit.Tag || '',
          actorName: edit.ActorName || '',
          text: chunkText(chunk),
          cleanText: cleanChunk(chunkText(chunk)),
          pause: chunk.Pause,
          startSecond: previousEnd,
          endSecond: end,
          modified: chunkKey(chunk) === 'ModifiedChunk' || Boolean(inspectionItem?.hasModifiedChunk),
          audioPath: inspectionItem?.audioPath,
          modifiedAudioPath: inspectionItem?.modifiedAudioPath,
        })
        if (end !== null) previousEnd = end
      })
    }
    return rows
  }

  function matchesChunkSearch(chunk, keywordSource = search) {
    const keyword = normalizeSearchValue(keywordSource)
    if (!keyword) return true
    const chunkNo = chunk.chunkIndex + 1
    const editMatch = keyword.match(/^edit(?:id)?[:\s-]*(\d+)$/)
    if (editMatch) return String(chunk.editId) === editMatch[1]
    const chunkMatch = keyword.match(/^chunk(?:id)?[:\s-]*(\d+)$/)
    if (chunkMatch) return String(chunkNo) === chunkMatch[1]
    const pairMatch = keyword.match(/^(\d+)[:\-](\d+)$/)
    if (pairMatch) return String(chunk.editId) === pairMatch[1] && String(chunkNo) === pairMatch[2]
    const haystack = normalizeSearchValue(
      [
        chunk.editId,
        chunkNo,
        `edit ${chunk.editId}`,
        `editid ${chunk.editId}`,
        `edit:${chunk.editId}`,
        `chunk ${chunkNo}`,
        `chunkid ${chunkNo}`,
        `chunk:${chunkNo}`,
        `${chunk.editId}-${chunkNo}`,
        `${chunk.editId}:${chunkNo}`,
        chunk.tag,
        chunk.actorName,
        chunk.cleanText,
        chunk.text,
      ].join(' '),
    )
    return haystack.includes(keyword)
  }

  function normalizeSearchValue(value) {
    return String(value || '').toLowerCase().replace(/\s+/g, ' ').trim()
  }

  function startsEditGroup(chunk, index) {
    if (index <= 0) return false
    return filteredChunks[index - 1]?.editIndex !== chunk.editIndex
  }

  function trackLabel(track) {
    if (!track) return '선택된 재생 없음'
    return track.label || track.name || 'Audio'
  }

  function selectedMetaLabel(chunk = selectedChunk) {
    if (!chunk) return 'Chunk 선택 없음'
    return `Edit ${chunk.editId} · Chunk ${chunk.chunkIndex + 1} · ${chunk.tag || 'Tag 없음'}`
  }

  function formatDuration(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return '-'
    const rounded = Math.max(0, Math.round(seconds))
    const hours = Math.floor(rounded / 3600)
    const minutes = Math.floor((rounded % 3600) / 60)
    const rest = String(rounded % 60).padStart(2, '0')
    if (hours) return `${hours}:${String(minutes).padStart(2, '0')}:${rest}`
    return `${minutes}:${rest}`
  }

  function progressStageFromLogs(logs) {
    const latest = [...(logs || [])].reverse().find(Boolean) || ''
    if (latest.includes('VoiceSplitSTTInspection')) return '분할 검수'
    if (latest.includes('RetryVoiceGen')) return '부분 재생성'
    if (latest.includes('VoiceSplit')) return '음성 분할'
    if (latest.includes('VoiceGen') || latest.includes('ChunkToSpeech')) return '음성 생성'
    if (latest.includes('SentsSpliting')) return '문장 분리'
    if (latest.includes('Process:')) {
      const match = latest.match(/Process:\s*([^|]+)/)
      return match?.[1]?.trim() || '처리 중'
    }
    return '준비 중'
  }

  function buildJobProgress(lock, logs, totalEdits, busy, now) {
    const running = Boolean(busy || lock?.running)
    const status = lock?.status || (running ? 'running' : 'idle')
    const startMs = Date.parse(lock?.startedAt || '')
    const elapsedSeconds = Number.isFinite(startMs) ? Math.max(0, (now - startMs) / 1000) : 0
    const editMarkers = new Set()

    for (const line of logs || []) {
      const chunkMatch = line.match(/ChunkToSpeech:[^,]*,\s*([0-9]+(?:\.[0-9]+)?):/)
      if (chunkMatch) editMarkers.add(chunkMatch[1])
      const retryMatch = line.match(/RetryVoiceGen.*?(\d+(?:\.\d+)?)/)
      if (retryMatch) editMarkers.add(retryMatch[1])
    }

    const editPercent = totalEdits > 0 && editMarkers.size > 0 ? (editMarkers.size / totalEdits) * 100 : 0
    const activityPercent = running ? Math.min(82, (logs?.length || 0) * 0.28) : 0
    let percent = Math.max(editPercent, activityPercent)

    if (running) {
      percent = Math.max(runStarting ? 2 : 4, Math.min(96, percent))
    } else if (status === 'completed') {
      percent = 100
    } else {
      percent = 0
    }

    const etaSeconds = running && percent > 5 ? (elapsedSeconds * (100 - percent)) / percent : null
    return {
      percent,
      percentText: `${Math.round(percent)}%`,
      elapsedText: formatDuration(elapsedSeconds),
      etaText: etaSeconds === null ? '계산 중' : formatDuration(etaSeconds),
      stage: progressStageFromLogs(logs),
      detail: editMarkers.size ? `${editMarkers.size}/${totalEdits || '?'} Edit 감지` : '로그 분석 중',
    }
  }

  function handleLogoError() {
    if (logoIndex < LOGO_CANDIDATES.length - 1) {
      logoIndex += 1
      return
    }
    logoMissing = true
  }

  async function loadProjects(selectFirst = true) {
    const payload = await request('/api/audiobook/projects')
    projects = payload.projects || []
    storageRoot = payload.storageRoot || ''
    if (!selected && selectFirst && projects.length) {
      const saved = savedProjectSelection()
      const savedProject = saved && projects.find((project) => project.email === saved.email && project.project === saved.project)
      await selectProject(savedProject || projects[0])
    }
    return projects
  }

  async function refreshWorkspace() {
    const previous = selected ? { email: selected.email, project: selected.project } : null
    const nextProjects = await loadProjects(false)
    if (!previous) {
      if (nextProjects.length) await selectProject(nextProjects[0])
      return
    }
    const stillExists = nextProjects.find((project) => project.email === previous.email && project.project === previous.project)
    if (stillExists) {
      selected = stillExists
      await loadProjectData(stillExists)
    } else if (nextProjects[0]) {
      await selectProject(nextProjects[0])
    } else {
      selected = null
      state = null
    }
  }

  async function loadAssets() {
    const [voices, musics] = await Promise.all([
      request('/api/audiobook/assets/voices'),
      request('/api/audiobook/assets/musics'),
    ])
    voiceAssets = voices.voices || []
    musicAssets = musics.musics || []
  }

  async function selectProject(project) {
    selected = project
    selectedChunkId = null
    localStorage.setItem(SELECTED_PROJECT_KEY, JSON.stringify({ email: project.email, project: project.project }))
    statusText = '프로젝트 로딩 중'
    await loadProjectData(project)
  }

  async function loadProjectData(project = selected) {
    if (!project) return
    const base = projectApiBase(project)
    loading = true
    closeLogStream()
    try {
      const [stateData, editData, voicesData, musicsData, inspectionData, configData] = await Promise.all([
        request(`${base}/state`),
        request(`${base}/edit`),
        request(`${base}/voices`),
        request(`${base}/musics`),
        request(`${base}/inspection`),
        request(`${base}/config`).catch((error) => ({ path: '', exists: false, data: {}, error: error.message })),
      ])
      state = stateData
      editPayload = editData
      voicesPayload = voicesData
      musicsPayload = musicsData
      configPayload = configData
      inspectionItems = inspectionData.items || []
      editDirty = false
      voiceDirty = false
      musicDirty = false
      configDirty = false
      statusText = stateData?.lock?.status === 'stopping'
        ? '종료 요청됨 · 현재 Edit 완료 대기'
        : (stateData?.lock?.running ? '생성 중 · 읽기 전용' : '준비 완료')
      if (stateData?.lock?.running && stateData?.lock?.logPath) openLogStream()
    } catch (error) {
      statusText = error.message
    } finally {
      loading = false
    }
  }

  async function saveEdit() {
    if (!selected || generationBusy) return
    saving = true
    try {
      await request(`${projectBase}/edit`, {
        method: 'PUT',
        body: JSON.stringify({ data: editPayload.data }),
      })
      editDirty = false
      statusText = 'Edit 저장 완료'
      await loadProjectData()
    } catch (error) {
      statusText = error.message
    } finally {
      saving = false
    }
  }

  async function saveVoices() {
    if (!selected || generationBusy) return
    saving = true
    try {
      await request(`${projectBase}/voices`, {
        method: 'PUT',
        body: JSON.stringify({ data: voicesPayload.data }),
      })
      voiceDirty = false
      statusText = 'Voice 저장 완료'
      await loadProjectData()
    } catch (error) {
      statusText = error.message
    } finally {
      saving = false
    }
  }

  async function saveMusics() {
    if (!selected || generationBusy) return
    saving = true
    try {
      await request(`${projectBase}/musics`, {
        method: 'PUT',
        body: JSON.stringify({ data: musicsPayload.data }),
      })
      musicDirty = false
      statusText = 'Music 저장 완료'
      await loadProjectData()
    } catch (error) {
      statusText = error.message
    } finally {
      saving = false
    }
  }

  async function saveConfig() {
    if (!selected || generationBusy) return
    saving = true
    try {
      await request(`${projectBase}/config`, {
        method: 'PUT',
        body: JSON.stringify({ data: configPayload.data }),
      })
      configDirty = false
      statusText = 'Config 저장 완료'
      await loadProjectData()
    } catch (error) {
      statusText = error.message
    } finally {
      saving = false
    }
  }

  async function runYaas() {
    if (!selected || generationBusy) return
    runStarting = true
    logsOpen = true
    statusText = 'YaaS 실행 요청 중'
    try {
      const runData = await request(`${projectBase}/run`, {
        method: 'POST',
        body: JSON.stringify({ messagesReview: 'on' }),
      })
      state = {
        ...(state || {}),
        lock: {
          ...(state?.lock || {}),
          running: true,
          status: 'running',
          pid: runData.pid,
          logPath: runData.logPath,
          startedAt: new Date().toISOString(),
        },
      }
      statusText = '생성 실행 중'
      openLogStream()
    } catch (error) {
      statusText = `실행 실패: ${error.message}`
    } finally {
      runStarting = false
    }
  }

  async function stopYaas() {
    if (!selected || !locked || stopping) return
    stopping = true
    logsOpen = true
    statusText = 'YaaS 종료 신호 전송 중'
    try {
      const stopData = await request(`${projectBase}/stop`, { method: 'POST', body: JSON.stringify({}) })
      state = {
        ...(state || {}),
        lock: stopData.lock || state?.lock,
      }
      statusText = stopData.running ? 'YaaS 종료 대기 중' : 'YaaS 종료 완료'
      await loadProjectData()
    } catch (error) {
      statusText = `종료 실패: ${error.message}`
    } finally {
      stopping = false
    }
  }

  async function releaseLock() {
    if (!selected || locked) return
    try {
      await request(`${projectBase}/lock/release`, { method: 'POST', body: JSON.stringify({}) })
      await loadProjectData()
      statusText = 'Lock 해제 완료'
    } catch (error) {
      statusText = error.message
    }
  }

  function updateActorName(edit, value) {
    edit.ActorName = value
    editDirty = true
    editPayload = editPayload
  }

  function updateTag(edit, value) {
    edit.Tag = value
    editDirty = true
    editPayload = editPayload
  }

  function selectChunkByKeyboard(event, chunkId) {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    selectedChunkId = chunkId
  }

  function updateArrayField(kind, index, key, rawValue, complex = false) {
    const payload = kind === 'voice' ? voicesPayload : musicsPayload
    const target = payload.data?.[index]
    if (!target) return
    const current = target[key]
    let next = rawValue
    if (complex) {
      try {
        next = JSON.parse(rawValue)
      } catch {
        statusText = `${key} JSON 형식 확인 필요`
        return
      }
    } else if (typeof current === 'number') {
      const numeric = Number(rawValue)
      next = Number.isFinite(numeric) ? numeric : rawValue
    } else if (typeof current === 'boolean') {
      next = rawValue === true || rawValue === 'true'
    }
    target[key] = next
    if (kind === 'voice') {
      voicesPayload = { ...voicesPayload, data: [...(voicesPayload.data || [])] }
      voiceDirty = true
    } else {
      musicsPayload = { ...musicsPayload, data: [...(musicsPayload.data || [])] }
      musicDirty = true
    }
  }

  function updateConfigField(key, rawValue, complex = false) {
    const current = configPayload.data?.[key]
    let next = rawValue
    if (complex) {
      try {
        next = JSON.parse(rawValue)
      } catch {
        statusText = `${key} JSON 형식 확인 필요`
        return
      }
    } else if (typeof current === 'number') {
      const numeric = Number(rawValue)
      next = Number.isFinite(numeric) ? numeric : rawValue
    } else if (typeof current === 'boolean') {
      next = rawValue === true || rawValue === 'true'
    }
    configPayload.data[key] = next
    configPayload = { ...configPayload, data: { ...(configPayload.data || {}) } }
    configDirty = true
  }

  function updateConfigNested(parentKey, key, rawValue, complex = false) {
    const parent = configPayload.data?.[parentKey]
    if (!parent || typeof parent !== 'object' || Array.isArray(parent)) return
    const current = parent[key]
    let next = rawValue
    if (complex) {
      try {
        next = JSON.parse(rawValue)
      } catch {
        statusText = `${parentKey}.${key} JSON 형식 확인 필요`
        return
      }
    } else if (typeof current === 'number') {
      const numeric = Number(rawValue)
      next = Number.isFinite(numeric) ? numeric : rawValue
    } else if (typeof current === 'boolean') {
      next = rawValue === true || rawValue === 'true'
    }
    parent[key] = next
    configPayload = { ...configPayload, data: { ...(configPayload.data || {}) } }
    configDirty = true
  }

  function isComplex(value) {
    return value !== null && typeof value === 'object'
  }

  function fieldValue(value) {
    if (value === null || value === undefined) return ''
    if (isComplex(value)) return JSON.stringify(value, null, 2)
    return String(value)
  }

  function closeLogStream() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  function openLogStream() {
    if (!selected) return
    closeLogStream()
    logLines = []
    eventSource = new EventSource(api(`${projectBase}/logs/stream`))
    eventSource.onmessage = (event) => {
      logLines = [...logLines.slice(-360), event.data]
    }
    eventSource.addEventListener('done', () => {
      closeLogStream()
      loadProjectData()
    })
    eventSource.onerror = () => {
      closeLogStream()
    }
  }

  function chunkTrack(chunk = selectedChunk) {
    if (!chunk?.audioPath) return null
    return {
      key: `chunk:${chunk.audioPath}:${chunk.id}`,
      label: selectedMetaLabel(chunk),
      sublabel: chunk.cleanText || chunk.text,
      path: chunk.audioPath,
      startAt: 0,
      endAt: null,
      chunkId: chunk.id,
      source: 'voice-chunk',
    }
  }

  function buildChunkPlaylist() {
    playlist = filteredChunks.map((chunk) => chunkTrack(chunk)).filter(Boolean)
  }

  async function playSelectedChunk(chunk = selectedChunk) {
    const track = chunkTrack(chunk)
    if (!track) {
      statusText = '선택 Chunk의 Voice WAV 파일이 없어 재생할 수 없습니다'
      return
    }
    selectedChunkId = chunk.id
    buildChunkPlaylist()
    await playTrack(track)
  }

  function waitForAudioReady() {
    if (!audioEl || audioEl.readyState >= 2) return Promise.resolve()
    return new Promise((resolve, reject) => {
      const cleanup = () => {
        audioEl?.removeEventListener('canplay', resolveReady)
        audioEl?.removeEventListener('loadedmetadata', resolveReady)
        audioEl?.removeEventListener('error', rejectReady)
      }
      const resolveReady = () => {
        cleanup()
        resolve()
      }
      const rejectReady = () => {
        cleanup()
        reject(new Error('오디오 파일을 불러오지 못했습니다'))
      }
      audioEl.addEventListener('canplay', resolveReady, { once: true })
      audioEl.addEventListener('loadedmetadata', resolveReady, { once: true })
      audioEl.addEventListener('error', rejectReady, { once: true })
    })
  }

  function scrollChunkIntoView(chunkId) {
    if (!chunkId) return
    for (const selector of [`[data-chunk-nav="${chunkId}"]`, `[data-chunk-editor="${chunkId}"]`]) {
      document.querySelector(selector)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }

  async function playTrack(track) {
    if (!track?.path) return
    currentTrack = track
    if (track.chunkId) selectedChunkId = track.chunkId
    pendingSeek = Number.isFinite(track.startAt) ? track.startAt : 0
    await tick()
    if (track.chunkId) scrollChunkIntoView(track.chunkId)
    if (audioEl) {
      audioEl.pause()
      syncAudioSettings()
      audioEl.load()
      try {
        await waitForAudioReady()
        syncAudioSettings()
        applyPendingSeek()
        await audioEl.play()
        statusText = 'Voice Chunk 재생 중'
      } catch (error) {
        statusText = error?.message || '브라우저가 자동 재생을 막았습니다'
      }
    }
  }

  function currentIndex() {
    return playlist.findIndex((track) => track.key === currentTrack?.key)
  }

  function playNext() {
    if (!playlist.length) return
    const next = currentIndex() + 1
    playTrack(playlist[next >= playlist.length ? 0 : next])
  }

  async function togglePlayback() {
    if (!currentTrack?.path || (selectedChunk?.id && currentTrack?.chunkId !== selectedChunk.id)) {
      await playSelectedChunk()
      return
    }
    if (!audioEl) return
    if (audioEl.paused) {
      try {
        syncAudioSettings()
        await audioEl.play()
      } catch {
        statusText = '브라우저가 자동 재생을 막았습니다'
      }
    } else {
      audioEl.pause()
    }
  }

  function setSpeed(speed) {
    playbackRate = speed
    syncAudioSettings()
  }

  function setVolume(value) {
    const next = Number(value)
    volume = Number.isFinite(next) ? Math.max(0, Math.min(1, next)) : 1
    syncAudioSettings()
  }

  function syncAudioSettings() {
    if (!audioEl) return
    audioEl.defaultPlaybackRate = playbackRate
    audioEl.playbackRate = playbackRate
    audioEl.volume = volume
  }

  function applyPendingSeek() {
    if (!audioEl || pendingSeek === null) return
    const target = Math.max(0, pendingSeek)
    try {
      audioEl.currentTime = target
      currentTime = target
      pendingSeek = null
    } catch {
      // Metadata may still be settling; the next metadata event will retry.
    }
  }

  function updateTime() {
    currentTime = audioEl?.currentTime || 0
  }

  function updateDuration() {
    syncAudioSettings()
    duration = Number.isFinite(audioEl?.duration) ? audioEl.duration : 0
    applyPendingSeek()
  }

  function handleCanPlay() {
    syncAudioSettings()
    applyPendingSeek()
  }

  function seekAudio(event) {
    const next = Number(event.currentTarget.value)
    if (audioEl && Number.isFinite(next)) {
      audioEl.currentTime = next
      currentTime = next
    }
  }

  function formatTime(value) {
    if (!Number.isFinite(value) || value <= 0) return '0:00'
    const hours = Math.floor(value / 3600)
    const minutes = Math.floor((value % 3600) / 60)
    const seconds = String(Math.floor(value % 60)).padStart(2, '0')
    if (hours) return `${hours}:${String(minutes).padStart(2, '0')}:${seconds}`
    return `${minutes}:${seconds}`
  }

  function handleEnded() {
    isPlaying = false
    playNext()
  }

  onMount(() => {
    const timer = window.setInterval(() => {
      nowMs = Date.now()
    }, 1000)

    ;(async () => {
      loading = true
      try {
        await Promise.all([loadProjects(), loadAssets()])
      } catch (error) {
        statusText = error.message
      } finally {
        loading = false
      }
    })()

    return () => {
      window.clearInterval(timer)
      closeLogStream()
    }
  })
</script>

<svelte:head>
  <title>STIDIO Workspace</title>
</svelte:head>

<main class:generating={generationBusy} class:logs-open={logsOpen} class:sidebar-collapsed={!sidebarOpen} class="studio-shell">
  <header class="studio-topbar">
    <div class="topbar-identity">
      <div class="topbar-brand">
        <img class:hidden={logoMissing} src={logoSrc} alt="STIDIO" on:error={handleLogoError} />
        <strong class:hidden={!logoMissing}>STIDIO</strong>
      </div>
    </div>
    <div class="topbar-status">
      {#if selected}
        <div class="topbar-metrics" aria-label="프로젝트 요약">
          <span class="project-chip"><strong>{selected.project}</strong></span>
          <span><em>Edit</em><strong>{state?.counts?.edits ?? '-'}</strong></span>
          <span><em>Chunk</em><strong>{state?.counts?.chunks ?? '-'}</strong></span>
          <span><em>Modified</em><strong>{modifiedCount}</strong></span>
          <span><em>Voice</em><strong>{state?.counts?.voiceAudio ?? '-'}</strong></span>
          <span><em>Master</em><strong>{masterCount}</strong></span>
        </div>
      {:else}
        <div class="topbar-metrics" aria-label="프로젝트 요약">
          <span class="project-chip"><strong>프로젝트 선택</strong></span>
        </div>
      {/if}
      <span class={generationBusy ? 'status-pill running' : 'status-pill ready'}>
        {#if generationBusy}<LockKeyhole size={13} />{:else}<BadgeCheck size={13} />{/if}
        {generationBusy ? '생성 중' : '편집 가능'}
      </span>
      {#if topbarStatusText}
        <span class="status-copy">{topbarStatusText}</span>
      {/if}
    </div>
    <div class="topbar-actions">
      <button class="icon-button topbar-refresh" title="프로젝트 새로고침" aria-label="프로젝트 새로고침" on:click={() => loadProjectData()} disabled={!selected || loading}>
        <RefreshCw size={15} />
      </button>
      <button class="button primary topbar-save" title={activeSaveTitle} on:click={activeSave.action} disabled={!selected || generationBusy || saving || !activeSave.dirty}>
        {activeSave.label}
      </button>
      {#if locked || stopping}
        <button class="button danger topbar-run" on:click={stopYaas} disabled={!selected || !locked || stopping}>
          <Pause size={14} />
          {stopping || state?.lock?.status === 'stopping' ? '종료 대기' : 'YaaS 멈춤'}
        </button>
      {:else}
        <button class="button primary topbar-run" on:click={runYaas} disabled={!selected || runStarting || loading}>
          <Rocket size={14} />
          {runStarting ? '실행 요청' : 'YaaS 실행'}
        </button>
      {/if}
    </div>
  </header>

  <aside class:collapsed={!sidebarOpen} class="studio-sidebar">
    {#if sidebarOpen}
      <section class="sidebar-tools">
        <span>Audiobook Workspace</span>
        <div class="sidebar-tool-buttons">
          <button class="sidebar-tool-button" title="프로젝트 목록 새로고침" on:click={refreshWorkspace}>
            <RefreshCw size={15} />
          </button>
        </div>
      </section>

      <section class="sidebar-card projects-card">
        <button class="sidebar-toggle" on:click={() => (projectsOpen = !projectsOpen)}>
          {#if projectsOpen}<ChevronDown size={14} />{:else}<ChevronRight size={14} />{/if}
          <FolderOpen size={14} />
          <span>Projects</span>
        </button>
        {#if projectsOpen}
          <div class="project-list">
            {#if projects.length === 0}
              <div class="empty">프로젝트 폴더가 없습니다.</div>
            {/if}
            {#each projects as project, projectIndex (`${project.email}/${project.project}:${projectIndex}`)}
              <button
                class:selected-project={selected?.email === project.email && selected?.project === project.project}
                class="project-row"
                on:click={() => selectProject(project)}
              >
                <span>{project.project}</span>
                <small>{project.email}</small>
              </button>
            {/each}
          </div>
        {/if}
      </section>

    {/if}
  </aside>

  <section class:locked-ui={generationBusy} class:has-progress={generationBusy} class="studio-main">
    {#if generationBusy}
      <section class="job-progress">
        <div class="progress-copy">
          <span>Generation Progress</span>
          <strong>{jobProgress.stage}</strong>
          <small>{jobProgress.detail} · 경과 {jobProgress.elapsedText} · 예상 남은 시간 {jobProgress.etaText}</small>
        </div>
        <div class="progress-meter" aria-label="YaaS 진행률">
          <i style={`width: ${jobProgress.percent}%`}></i>
        </div>
        <strong class="progress-percent">{jobProgress.percentText}</strong>
      </section>
    {/if}

    {#if selected}
      <section class:locked-panel={generationBusy} class="workbench">
        <div class="workbench-head">
          <nav class="panel-tabs" aria-label="워크스페이스 패널">
            <button class:active={activePanel === 'Edit'} on:click={() => (activePanel = 'Edit')}>
              <FilePenLine size={14} />
              Edit
            </button>
            <button class:active={activePanel === 'Voice'} on:click={() => (activePanel = 'Voice')}>
              <Mic2 size={14} />
              Voice
            </button>
            <button class:active={activePanel === 'Music'} on:click={() => (activePanel = 'Music')}>
              <Music2 size={14} />
              Music
            </button>
            <button class:active={activePanel === 'Config'} on:click={() => (activePanel = 'Config')}>
              <Settings2 size={14} />
              Config
            </button>
          </nav>

          <label class="search-box">
            <Search size={15} />
            <input placeholder="EditId, ChunkId, 성우, 문장 검색" bind:value={search} />
          </label>
        </div>

        {#if generationBusy}
          <div class="lock-banner">
            <LockKeyhole size={14} />
            생성 프로세스가 실행 중입니다. Edit, Voice, Music, Config는 읽기 전용으로 잠겨 있고 로그와 진행률만 갱신됩니다.
          </div>
        {/if}

        {#if activePanel === 'Edit'}
          <div class="edit-workspace">
            <aside class="chunk-index">
              {#each filteredChunks as chunk, chunkPosition (`${chunk.id}`)}
                <div
                  role="button"
                  tabindex="0"
                  class:selected-chunk={selectedChunkId === chunk.id}
                  class:modified={chunk.modified}
                  class:edit-break={startsEditGroup(chunk, chunkPosition)}
                  class="chunk-index-row"
                  data-chunk-nav={chunk.id}
                  on:click={() => (selectedChunkId = chunk.id)}
                  on:keydown={(event) => selectChunkByKeyboard(event, chunk.id)}
                >
                  <strong class="chunk-number">{chunk.editId}</strong>
                  <input
                    class="tag-name-input"
                    readonly={generationBusy}
                    value={chunk.tag || ''}
                    aria-label={`Edit ${chunk.editId} Tag`}
                    on:click|stopPropagation={() => (selectedChunkId = chunk.id)}
                    on:focus={() => (selectedChunkId = chunk.id)}
                    on:input={(event) => updateTag(chunk.edit, event.currentTarget.value)}
                  />
                  <span class="chunk-number">{chunk.chunkIndex + 1}</span>
                  <input
                    class="actor-name-input"
                    readonly={generationBusy}
                    value={chunk.actorName || ''}
                    aria-label={`Edit ${chunk.editId} ActorName`}
                    on:click|stopPropagation={() => (selectedChunkId = chunk.id)}
                    on:focus={() => (selectedChunkId = chunk.id)}
                    on:input={(event) => updateActorName(chunk.edit, event.currentTarget.value)}
                  />
                </div>
              {/each}
            </aside>

            <section class="chunk-editor-pane">
              <div class="text-editor-sheet">
                {#each filteredChunks as chunk, chunkPosition (`editor:${chunk.id}`)}
                  <div
                    role="button"
                    tabindex="0"
                    class:selected-line={selectedChunkId === chunk.id}
                    class:edit-break={startsEditGroup(chunk, chunkPosition)}
                    class="text-line"
                    data-chunk-editor={chunk.id}
                    title={`${selectedMetaLabel(chunk)} · ${formatTime(chunk.startSecond)}부터`}
                    on:click={() => (selectedChunkId = chunk.id)}
                    on:keydown={(event) => selectChunkByKeyboard(event, chunk.id)}
                  >
                    <textarea
                      rows="1"
                      readonly={generationBusy}
                      value={chunk.text}
                      aria-label={`${selectedMetaLabel(chunk)} text`}
                      on:focus={() => (selectedChunkId = chunk.id)}
                      on:input={(event) => setChunkText(chunk.chunk, event.currentTarget.value)}
                    ></textarea>
                  </div>
                {/each}
              </div>
            </section>
          </div>
        {:else if activePanel === 'Voice'}
          <div class="structured-panel">
            <section class="record-list">
              {#each voicesPayload.data || [] as voice, index (`voice:${index}:${voice.ActorName || voice.CharacterTag || ''}`)}
                <article class="record-card">
                  <h3>{voice.ActorName || voice.CharacterTag || `Voice ${index + 1}`}</h3>
                  <div class="field-grid">
                    {#each Object.entries(voice) as [key, value]}
                      <label class:wide={isComplex(value)}>
                        <span>{key}</span>
                        {#if isComplex(value)}
                          <textarea rows="5" readonly={generationBusy} value={fieldValue(value)} on:change={(event) => updateArrayField('voice', index, key, event.currentTarget.value, true)}></textarea>
                        {:else}
                          <input readonly={generationBusy} value={fieldValue(value)} on:input={(event) => updateArrayField('voice', index, key, event.currentTarget.value)} />
                        {/if}
                      </label>
                    {/each}
                  </div>
                </article>
              {/each}
            </section>
            <aside class="asset-list">
              <h3>성우 리스트</h3>
              {#each voiceAssets as voice, voiceIndex (`${voice.CharacterId}:${voiceIndex}`)}
                <div class="asset-row">
                  <strong>{voice.Name}</strong>
                  <span>{voice.ApiSetting?.Api || 'API 미지정'}</span>
                  <small>{voice.ApiSetting?.voice_name || voice.ApiSetting?.voice_id || voice.SamplePath}</small>
                </div>
              {/each}
            </aside>
          </div>
        {:else if activePanel === 'Music'}
          <div class="structured-panel">
            <section class="record-list">
              {#each musicsPayload.data || [] as music, index (`music:${index}:${music.Tag || music.File || ''}`)}
                <article class="record-card">
                  <h3>{music.Tag || music.File || `Music ${index + 1}`}</h3>
                  <div class="field-grid">
                    {#each Object.entries(music) as [key, value]}
                      <label class:wide={isComplex(value)}>
                        <span>{key}</span>
                        {#if isComplex(value)}
                          <textarea rows="5" readonly={generationBusy} value={fieldValue(value)} on:change={(event) => updateArrayField('music', index, key, event.currentTarget.value, true)}></textarea>
                        {:else}
                          <input readonly={generationBusy} value={fieldValue(value)} on:input={(event) => updateArrayField('music', index, key, event.currentTarget.value)} />
                        {/if}
                      </label>
                    {/each}
                  </div>
                </article>
              {/each}
            </section>
            <aside class="asset-list">
              <h3>음악 리스트</h3>
              {#each musicAssets.slice(0, 240) as music, musicIndex (`${music.relativePath}:${musicIndex}`)}
                <div class="asset-row">
                  <strong>{music.name}</strong>
                  <span>{music.category}</span>
                  <small>{music.relativePath}</small>
                </div>
              {/each}
            </aside>
          </div>
        {:else}
          <div class="config-panel">
            {#if configPayload.error}
              <div class="notice">백엔드 재시작 후 Config API가 연결됩니다. 현재 오류: {configPayload.error}</div>
            {/if}
            {#each Object.entries(configPayload.data || {}) as [key, value]}
              <article class="record-card">
                <h3>{key}</h3>
                {#if isComplex(value) && !Array.isArray(value)}
                  <div class="field-grid">
                    {#each Object.entries(value) as [innerKey, innerValue]}
                      <label class:wide={isComplex(innerValue)}>
                        <span>{innerKey}</span>
                        {#if isComplex(innerValue)}
                          <textarea rows="5" readonly={generationBusy} value={fieldValue(innerValue)} on:change={(event) => updateConfigNested(key, innerKey, event.currentTarget.value, true)}></textarea>
                        {:else}
                          <input readonly={generationBusy} value={fieldValue(innerValue)} on:input={(event) => updateConfigNested(key, innerKey, event.currentTarget.value)} />
                        {/if}
                      </label>
                    {/each}
                  </div>
                {:else}
                  <label class:wide={isComplex(value)} class="single-field">
                    <span>{key}</span>
                    {#if isComplex(value)}
                      <textarea rows="6" readonly={generationBusy} value={fieldValue(value)} on:change={(event) => updateConfigField(key, event.currentTarget.value, true)}></textarea>
                    {:else}
                      <input readonly={generationBusy} value={fieldValue(value)} on:input={(event) => updateConfigField(key, event.currentTarget.value)} />
                    {/if}
                  </label>
                {/if}
              </article>
            {/each}
          </div>
        {/if}
      </section>
    {:else}
      <div class="no-project">
        <h2>프로젝트 폴더를 기다리는 중</h2>
        <p>/yaas/storage/s1_Yeoreum 아래에 프로젝트가 추가되면 새로고침으로 바로 표시됩니다.</p>
      </div>
    {/if}
  </section>
</main>

<footer class:logs-open={logsOpen} class="studio-dock">
  <section class="studio-player">
    <section class="player-left">
      <button
        class="sidebar-dock-toggle"
        title={sidebarOpen ? '프로젝트 패널 접기' : '프로젝트 패널 펼치기'}
        on:click={() => (sidebarOpen = !sidebarOpen)}
      >
        {#if sidebarOpen}<PanelLeftClose size={15} />{:else}<PanelLeftOpen size={15} />{/if}
      </button>

      <section class="now-playing">
        <strong>{trackLabel(currentTrack)}</strong>
        {#if currentTrack?.sublabel}
          <small>{currentTrack.sublabel}</small>
        {/if}
      </section>
    </section>

    <section class="transport">
      <button class="play-button" title={isPlaying ? '일시정지' : '재생'} disabled={!currentTrack && !selectedChunk?.audioPath} on:click={togglePlayback}>
        {#if isPlaying}<Pause size={19} fill="currentColor" />{:else}<Play size={19} fill="currentColor" />{/if}
      </button>
      <div class="time-rail">
        <span>{formatTime(currentTime)}</span>
        <input type="range" min="0" max={duration || 0} step="0.1" value={currentTime} on:input={seekAudio} />
        <span>{formatTime(duration)}</span>
      </div>
    </section>

    <section class="player-right">
      <label class="volume-control" title={`볼륨 ${Math.round(volume * 100)}%`}>
        <Volume2 size={15} />
        <input type="range" min="0" max="1" step="0.01" value={volume} on:input={(event) => setVolume(event.currentTarget.value)} />
      </label>
      <div class="speed">
        {#each speeds as speed}
          <button class:active={playbackRate === speed} on:click={() => setSpeed(speed)}>{speed}x</button>
        {/each}
      </div>
      <button class="terminal-toggle" title="로그" on:click={() => (logsOpen = !logsOpen)}>
        &gt;_
      </button>
    </section>
  </section>

  {#if logsOpen}
    <section class="log-drawer">
      <div class="log-head">
        <h2><Terminal size={15} /> Logs</h2>
        <div>
          <button class="mini-button" on:click={openLogStream} disabled={!selected}>연결</button>
          {#if locked}
            <button class="mini-button danger" on:click={stopYaas} disabled={stopping}>{stopping || state?.lock?.status === 'stopping' ? '종료 대기' : 'YaaS 멈춤'}</button>
          {/if}
        </div>
      </div>
      <pre class="logs">{logLines.length ? logLines.join('\n') : '로그 스트림 대기 중'}</pre>
    </section>
  {/if}

  <audio
    bind:this={audioEl}
    src={currentAudioSrc}
    on:timeupdate={updateTime}
    on:loadedmetadata={updateDuration}
    on:canplay={handleCanPlay}
    on:error={() => (statusText = '오디오 파일 로딩 실패')}
    on:play={() => (isPlaying = true)}
    on:pause={() => (isPlaying = false)}
    on:ended={handleEnded}
  ></audio>
</footer>
