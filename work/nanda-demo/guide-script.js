
  document.querySelectorAll('.copy').forEach(button => {
    button.addEventListener('click', async () => {
      const card = button.closest('.prompt-card, .inline-prompt');
      const prompt = card.querySelector('.prompt');
      const text = prompt.textContent.trim();
      let copied = false;
      try { await navigator.clipboard.writeText(text); copied = true; } catch (_) {
        const field = document.createElement('textarea');
        field.value = text; field.setAttribute('aria-hidden','true');
        field.style.cssText = 'position:fixed;left:-9999px;top:0';
        document.body.appendChild(field); field.select();
        try { copied = document.execCommand('copy'); } catch (_) {}
        field.remove(); button.focus();
      }
      if (copied) {
        button.textContent = 'Copied';
        document.getElementById('copy-status').textContent = 'Prompt copied. Replace the text in brackets before sending.';
        setTimeout(() => button.textContent = 'Copy', 2000);
      } else {
        const selection = window.getSelection(); const range = document.createRange();
        range.selectNodeContents(prompt); selection.removeAllRanges(); selection.addRange(range);
        document.getElementById('copy-status').textContent = 'Select and copy the highlighted prompt.';
        button.textContent = 'Select & copy';
      }
    });
  });
  const dialog = document.getElementById('image-dialog');
  document.querySelectorAll('.shot').forEach(link => link.addEventListener('click', event => {
    if (typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    const picture = link.querySelector('img');
    document.getElementById('dialog-image').src = picture.src;
    document.getElementById('dialog-image').alt = picture.alt;
    document.getElementById('image-caption').textContent = link.dataset.caption;
    dialog.showModal();
  }));
  document.getElementById('close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
