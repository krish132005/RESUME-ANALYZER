document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const resultsSection = document.getElementById('results-section');
    const heroSection = document.querySelector('.hero');
    const loader = document.getElementById('loader');
    const resetBtn = document.getElementById('reset-btn');

    // UI Elements for Data Injection
    const resName = document.getElementById('res-name');
    const resTitle = document.getElementById('res-title');
    const resContact = document.getElementById('res-contact');
    const resExperience = document.getElementById('res-experience');
    const resEducation = document.getElementById('res-education');
    const resSkills = document.getElementById('res-skills');
    const resMeta = document.getElementById('res-meta');

    // Trigger file input on click
    browseBtn.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag and Drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
    });

    resetBtn.addEventListener('click', () => {
        resultsSection.classList.add('results-hidden');
        heroSection.style.display = 'block';
        fileInput.value = '';
    });

    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Show Loader
        loader.classList.remove('loader-hidden');
        
        try {
            const response = await fetch('/parse', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to parse resume');

            const data = await response.json();
            renderResults(data);
        } catch (error) {
            console.error(error);
            alert('Error parsing resume. Please try a different file format.');
        } finally {
            loader.classList.add('loader-hidden');
        }
    }

    function renderResults(data) {
        // Hide Hero, Show Results
        heroSection.style.display = 'none';
        resultsSection.classList.remove('results-hidden');

        // Basic Info
        resName.textContent = data.candidate_name || 'Name Not Found';
        resTitle.textContent = (data.experience && data.experience[0]) ? data.experience[0].title : 'Candidate';

        // Contact Info
        resContact.innerHTML = '';
        const contact = data.contact || {};
        
        if (contact.emails?.length) {
            resContact.appendChild(createContactItem('mail', contact.emails[0]));
        }
        if (contact.phones?.length) {
            resContact.appendChild(createContactItem('phone', contact.phones[0]));
        }
        if (contact.linkedin) {
            resContact.appendChild(createContactItem('linkedin', contact.linkedin, true));
        }
        if (contact.github) {
            resContact.appendChild(createContactItem('github', contact.github, true));
        }

        // Skills
        resSkills.innerHTML = '';
        if (data.skills) {
            Object.entries(data.skills).forEach(([category, skills]) => {
                if (skills.length === 0) return;
                const div = document.createElement('div');
                div.className = 'skill-category';
                div.innerHTML = `
                    <h4>${category}</h4>
                    <div class="pills">
                        ${skills.map(s => `<span class="pill">${s}</span>`).join('')}
                    </div>
                `;
                resSkills.appendChild(div);
            });
        }

        // Experience
        resExperience.innerHTML = '';
        if (data.experience?.length) {
            data.experience.forEach(exp => {
                const item = document.createElement('div');
                item.className = 'timeline-item';
                item.innerHTML = `
                    <div class="entry-header">
                        <div class="entry-title">${exp.title}</div>
                        <div class="entry-dates">${exp.dates?.start_date} - ${exp.dates?.end_date}</div>
                    </div>
                    <div class="entry-meta">${exp.company}</div>
                    <div class="entry-desc">${exp.description}</div>
                `;
                resExperience.appendChild(item);
            });
        } else {
            resExperience.innerHTML = '<p class="text-muted">No experience entries found.</p>';
        }

        // Education
        resEducation.innerHTML = '';
        if (data.education?.length) {
            data.education.forEach(edu => {
                const item = document.createElement('div');
                item.className = 'edu-item';
                item.innerHTML = `
                    <div class="entry-header">
                        <div class="entry-title">${edu.degree || 'Degree Not Specified'}</div>
                        <div class="entry-dates">${edu.dates?.start_date || ''} - ${edu.dates?.end_date || ''}</div>
                    </div>
                    <div class="entry-meta">${edu.institution} ${edu.gpa ? `• GPA: ${edu.gpa}` : ''}</div>
                    <div class="entry-desc">${edu.details || ''}</div>
                `;
                resEducation.appendChild(item);
            });
        }

        // Meta (Certifications, Awards, Languages)
        resMeta.innerHTML = '';
        ['certifications', 'awards', 'languages'].forEach(key => {
            if (data[key]) {
                const div = document.createElement('div');
                div.className = 'skill-category';
                div.innerHTML = `
                    <h4>${key.charAt(0).toUpperCase() + key.slice(1)}</h4>
                    <p style="font-size: 0.9rem; color: var(--text-muted); white-space: pre-line;">${data[key]}</p>
                `;
                resMeta.appendChild(div);
            }
        });

        // Re-initialize icons
        lucide.createIcons();
    }

    function createContactItem(icon, text, isLink = false) {
        const div = document.createElement('div');
        div.className = 'contact-item';
        div.innerHTML = `
            <i data-lucide="${icon}"></i>
            ${isLink ? `<a href="${text.startsWith('http') ? text : 'https://' + text}" target="_blank">${text.split('/').pop()}</a>` : `<span>${text}</span>`}
        `;
        return div;
    }
});
