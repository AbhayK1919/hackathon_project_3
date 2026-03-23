// Gen Z Theme Toggle + Interactions
document.addEventListener('DOMContentLoaded', () => {
  // Load theme
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  
  // Theme toggle
  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const newTheme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }

  // Navbar mobile collapse
  const navbarToggle = document.querySelector('.navbar-toggler');
  if (navbarToggle) {
    navbarToggle.onclick = () => {
      document.querySelector('.navbar-collapse').classList.toggle('show');
    };
  }

  // File upload feedback
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.onchange = () => {
      const label = input.nextElementSibling || input.parentNode.querySelector('button');
      label.textContent = 'Uploading...';
      label.classList.add('loading');
      
      setTimeout(() => {
        label.textContent = 'Upload Complete! ✨';
        label.classList.remove('loading');
        setTimeout(() => {
          label.textContent = 'Upload & Classify';
        }, 1500);
      }, 2000);
    };
  });

  // Confetti on upload success (simple CSS)
  function triggerConfetti() {
    // Create canvas particles
    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999';
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: canvas.height + 100,
        vx: (Math.random() - 0.5) * 10,
        vy: Math.random() * -15 - 5,
        color: ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6'][Math.floor(Math.random()*5)],
        size: Math.random() * 5 + 3
      });
    }
    
    let frame = 0;
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.2;
        p.rotation += 0.1;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size);
        ctx.restore();
      });
      if (++frame < 80) requestAnimationFrame(animate);
      else canvas.remove();
    }
    animate();
  }

// Auto-trigger confetti on form submit
  document.querySelectorAll('form[enctype]').forEach(form => {
    form.onsubmit = triggerConfetti;
  });

  // Camera capture for files.html
  const cameraBtn = document.getElementById('cameraBtn');
  const fileInput = document.getElementById('fileInput');
  const cameraPreview = document.getElementById('cameraPreview');
  const cameraCanvas = document.getElementById('cameraCanvas');
  let stream = null;

  if (cameraBtn) {
    cameraBtn.onclick = async () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        cameraBtn.textContent = '📸 Camera';
        cameraBtn.style.display = 'none';
        cameraPreview.style.display = 'none';
        return;
      }

      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        cameraPreview.srcObject = stream;
        cameraPreview.style.display = 'block';
        cameraBtn.textContent = '📷 Capture';
        cameraBtn.style.display = 'block';

        // Capture photo
        setTimeout(() => {
  if (cameraPreview.style.display === 'block') {
            const context = cameraCanvas.getContext('2d');
            cameraCanvas.width = cameraPreview.videoWidth;
            cameraCanvas.height = cameraPreview.videoHeight;
            context.drawImage(cameraPreview, 0, 0);
            
            // Create file from canvas
            cameraCanvas.toBlob((blob) => {
              const file = new File([blob], 'screenshot.jpg', { type: 'image/jpeg' });
              const dt = new DataTransfer();
              dt.items.add(file);
              fileInput.files = dt.files;
              
              // OCR Preview
              OCRPreview(file);
              
              cameraPreview.style.display = 'none';
              cameraBtn.textContent = '📸 Camera';
            }, 'image/jpeg');
          }
        }, 3000); // Auto-capture after 3s
      } catch (err) {
        alert('Camera access denied. Use file upload instead.');
      }
    };
  }

  // OCR Preview for images
  function OCRPreview(file) {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        Tesseract.recognize(e.target.result, 'eng', {
          logger: m => console.log(m)
        }).then(({ data: { text } }) => {
          alert(`📝 Extracted Text Preview:\n\n${text.substring(0, 200)}...\n\nUpload to save with notes!`);
        }).catch(err => {
          console.error('OCR failed:', err);
        });
      };
      reader.readAsDataURL(file);
    }
  }
getComputedStyle
  // Trigger OCR on file select if image
  fileInput?.addEventListener('change', (e) => {
    if (e.target.files[0]?.type.startsWith('image/')) {
      OCRPreview(e.target.files[0]);
    }
  });

  // Smooth scroll & active nav
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      e.preventDefault();
      document.querySelector(anchor.getAttribute('href')).scrollIntoView({behavior: 'smooth'});
    });
  });
});

exit(0);
{
  process.exit(0);
}


