const form = document.getElementById('resume-form')
const fileInput = document.getElementById('file')
const textInput = document.getElementById('text')
const output = document.getElementById('output')
const API_URL = 'http://127.0.0.1:8001'
let requestId = 0

fileInput.addEventListener('change', () => {
  requestId += 1
  output.textContent = fileInput.files.length
    ? `Ready to analyze: ${fileInput.files[0].name}`
    : 'No results yet.'
})

form.addEventListener('submit', async (e) => {
  e.preventDefault()
  const currentRequest = requestId + 1
  requestId = currentRequest
  output.textContent = 'Analyzing...'
  const fd = new FormData()
  if (fileInput.files.length > 0) fd.append('resume', fileInput.files[0])
  if (textInput.value.trim()) fd.append('text', textInput.value.trim())

  try {
    const res = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body: fd })
    const json = await res.json()
    if (currentRequest !== requestId) return
    output.textContent = JSON.stringify(json, null, 2)
  } catch (err) {
    if (currentRequest !== requestId) return
    output.textContent = 'Request failed: ' + err
  }
})
