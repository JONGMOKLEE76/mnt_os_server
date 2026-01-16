document.addEventListener('DOMContentLoaded', () => {
    const diaryList = document.getElementById('diary-list');
    const entryDetail = document.getElementById('entry-detail');
    const entryForm = document.getElementById('entry-form');
    const editor = document.getElementById('editor');
    const authorActions = document.getElementById('author-actions');
    const deleteEntryBtn = document.getElementById('delete-entry-btn');
    const saveEntryBtn = document.getElementById('save-entry-btn');

    // Filters
    const statusFilter = document.getElementById('status-filter');
    const authorSearch = document.getElementById('author-search');
    const keywordSearch = document.getElementById('keyword-search');
    const fromDate = document.getElementById('from-date');
    const toDate = document.getElementById('to-date');
    const searchBtn = document.getElementById('search-btn');

    // Comments
    const commentInput = document.getElementById('comment-input');
    const submitComment = document.getElementById('submit-comment');
    const commentsList = document.getElementById('comments-list');
    const emojiBtns = document.querySelectorAll('.emoji-btn');

    let currentFilters = {
        status: '',
        author: '',
        keyword: '',
        from_date: '',
        to_date: '',
        hashtag: new URLSearchParams(window.location.search).get('hashtag') || ''
    };

    // Load entries if on list page
    if (diaryList) {
        loadEntries();
    }

    // Load entry detail if on detail page
    const currentEntryId = typeof ENTRY_ID !== 'undefined' ? ENTRY_ID : null;
    if (entryDetail && currentEntryId) {
        loadEntryDetail();
    }

    async function loadEntries() {
        const params = new URLSearchParams();
        if (currentFilters.status) params.append('status', currentFilters.status);
        if (currentFilters.author) params.append('author', currentFilters.author);
        if (currentFilters.keyword) params.append('keyword', currentFilters.keyword);
        if (currentFilters.hashtag) params.append('hashtag', currentFilters.hashtag);
        if (currentFilters.from_date) params.append('from_date', currentFilters.from_date);
        if (currentFilters.to_date) params.append('to_date', currentFilters.to_date);

        try {
            const response = await fetch(`/api/work-diary?${params.toString()}`);
            const data = await response.json();
            renderEntries(data);
        } catch (error) {
            console.error('Error loading entries:', error);
        }
    }

    function renderEntries(entries) {
        if (entries.length === 0) {
            diaryList.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No entries found.</div>';
            return;
        }

        diaryList.innerHTML = entries.map(entry => `
            <div class="diary-item" onclick="location.href='/work-diary/${entry.id}'">
                <div class="diary-info">
                    <h3>${entry.title}</h3>
                    <div class="diary-meta">
                        <span><i class="fas fa-user"></i> ${entry.author}</span>
                        <span><i class="fas fa-calendar-alt"></i> ${entry.created_at}</span>
                        <span class="diary-status status-${entry.status}">${entry.status}</span>
                    </div>
                </div>
                <div class="diary-stats">
                    <span><i class="fas fa-comment"></i> ${entry.comment_count}</span>
                    <i class="fas fa-chevron-right"></i>
                </div>
            </div>
        `).join('');
    }

    async function loadEntryDetail() {
        try {
            const response = await fetch(`/api/work-diary/${currentEntryId}`);
            const data = await response.json();

            const hashtagsHtml = data.hashtags ? data.hashtags.split(',').map(tag =>
                `<span class="hashtag-link" onclick="filterByHashtag('${tag.trim().replace('#', '')}')">${tag.trim()}</span>`
            ).join(' ') : '';

            entryDetail.innerHTML = `
                <div class="entry-header">
                    <h1 id="detail-title" class="entry-title" ${data.is_author ? 'contenteditable="true"' : ''}>${data.title}</h1>
                    <div class="entry-meta">
                        <span><i class="fas fa-user"></i> ${data.author}</span>
                        <span><i class="fas fa-calendar-alt"></i> ${data.created_at}</span>
                        <span class="diary-status status-${data.status}">${data.status}</span>
                        <div class="hashtags-container">${hashtagsHtml}</div>
                    </div>
                </div>
                <div id="detail-content" class="entry-content" ${data.is_author ? 'contenteditable="true"' : ''}>
                    ${data.content}
                </div>
            `;

            if (data.is_author && authorActions) {
                authorActions.style.display = 'flex';
            }

            renderComments(data.comments);
            window.currentEntryData = data;
        } catch (error) {
            console.error('Error loading entry detail:', error);
        }
    }

    window.filterByHashtag = (tag) => {
        location.href = `/work-diary?hashtag=${tag}`;
    };

    function renderComments(comments) {
        if (!commentsList) return;
        commentsList.innerHTML = comments.map(c => `
            <div class="comment-item">
                <div class="comment-header">
                    <span class="comment-author">${c.author}</span>
                    <span class="comment-date">${c.created_at}</span>
                </div>
                <div class="comment-content">${c.content}</div>
            </div>
        `).join('');
    }

    // Image Paste Handling (Ctrl+V)
    const handlePaste = async (e) => {
        const target = e.currentTarget;
        if (target.getAttribute('contenteditable') !== 'true' && target.id !== 'editor') return;

        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        let imageFound = false;

        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                imageFound = true;
                const blob = item.getAsFile();
                const reader = new FileReader();
                reader.onload = async (event) => {
                    const base64Image = event.target.result;
                    try {
                        const response = await fetch('/api/upload-image', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ image: base64Image })
                        });
                        const result = await response.json();
                        if (result.url) {
                            const img = document.createElement('img');
                            img.src = result.url;

                            const selection = window.getSelection();
                            if (selection.rangeCount > 0) {
                                const range = selection.getRangeAt(0);
                                range.deleteContents();
                                range.insertNode(img);
                                // Move cursor after image
                                range.setStartAfter(img);
                                range.setEndAfter(img);
                                selection.removeAllRanges();
                                selection.addRange(range);
                            } else {
                                target.appendChild(img);
                            }
                        }
                    } catch (error) {
                        console.error('Error uploading image:', error);
                    }
                };
                reader.readAsDataURL(blob);
            }
        }

        if (imageFound) {
            e.preventDefault();
        }
    };

    if (editor) editor.addEventListener('paste', handlePaste);
    if (entryDetail) entryDetail.addEventListener('paste', handlePaste);

    // Save Changes (Inline Edit)
    if (saveEntryBtn) {
        saveEntryBtn.addEventListener('click', async () => {
            const title = document.getElementById('detail-title').innerText;
            const content = document.getElementById('detail-content').innerHTML;

            try {
                const response = await fetch(`/api/work-diary/${currentEntryId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
                });
                if (response.ok) {
                    alert('Changes saved successfully!');
                    loadEntryDetail();
                } else {
                    alert('Failed to save changes');
                }
            } catch (error) {
                console.error('Error saving changes:', error);
            }
        });
    }

    // Delete Entry
    if (deleteEntryBtn) {
        deleteEntryBtn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to delete this entry?')) return;
            try {
                const response = await fetch(`/api/work-diary/${currentEntryId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    location.href = '/work-diary';
                }
            } catch (error) {
                console.error('Error deleting entry:', error);
            }
        });
    }

    // Create New Entry (Full Page)
    if (entryForm && !currentEntryId) {
        entryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(entryForm);
            const data = Object.fromEntries(formData.entries());
            data.content = editor.innerHTML;

            try {
                const response = await fetch('/api/work-diary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (result.id) {
                    location.href = `/work-diary/${result.id}`;
                } else {
                    alert(result.error || 'Failed to create entry');
                }
            } catch (error) {
                console.error('Error creating entry:', error);
            }
        });
    }

    // Search and Filters
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            currentFilters.status = statusFilter.value;
            currentFilters.author = authorSearch.value;
            currentFilters.keyword = keywordSearch.value;
            currentFilters.from_date = fromDate.value;
            currentFilters.to_date = toDate.value;
            currentFilters.hashtag = '';
            loadEntries();
        });
    }

    // Comments and Emojis
    if (submitComment) {
        submitComment.addEventListener('click', async () => {
            const content = commentInput.value.trim();
            if (!content) return;

            try {
                const response = await fetch(`/api/work-diary/${currentEntryId}/comments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                if (response.ok) {
                    commentInput.value = '';
                    loadEntryDetail();
                }
            } catch (error) {
                console.error('Error posting comment:', error);
            }
        });
    }

    emojiBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            commentInput.value += btn.innerText;
            commentInput.focus();
        });
    });
});
