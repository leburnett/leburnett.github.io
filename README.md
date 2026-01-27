# Personal Website Documentation

Welcome! This guide will help you customize and deploy your personal website.

## 📁 Project Structure

```
your-website/
├── index.html          # Main HTML file (structure and content)
├── styles.css          # CSS stylesheet (design and layout)
├── script.js           # JavaScript file (interactivity)
├── images/             # Folder for your images (create this)
│   ├── profile.jpg     # Your profile photo
│   ├── project1.jpg    # Project images
│   ├── project2.jpg
│   └── project3.jpg
└── README.md           # This documentation file
```

---

## 🎨 Quick Start: Personalizing Your Website

### Step 1: Update Basic Information

Open `index.html` and search for the following placeholders. Replace them with your information:

| Placeholder | What to Replace | Where to Find |
|------------|----------------|---------------|
| `[Your Name]` | Your full name | Throughout the file |
| `[Your Profession]` | Your job title/field | Hero section |
| `[Your Institution/Company]` | Where you work/study | Hero and contact sections |
| `your.email@example.com` | Your actual email | Multiple locations |
| `yourusername` | Your GitHub/LinkedIn username | Social links |

**Tip:** Use Find & Replace (Ctrl+F or Cmd+F) to update all instances at once!

### Step 2: Customize Colors and Fonts

Open `styles.css` and scroll to the **CSS VARIABLES** section at the top. Change these values:

```css
:root {
    /* Change these colors to match your brand */
    --primary-color: #2c5f7c;      /* Main brand color */
    --secondary-color: #e67e22;    /* Accent color */
    
    /* Change fonts if you want different typography */
    --font-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', ...;
    --font-heading: 'Georgia', 'Times New Roman', serif;
}
```

**Color Picker Tools:**
- [Coolors.co](https://coolors.co/) - Generate color palettes
- [Adobe Color](https://color.adobe.com/) - Color wheel and themes

**Font Resources:**
- [Google Fonts](https://fonts.google.com/) - Free web fonts
- To use a Google Font, add this to your `<head>` in `index.html`:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  ```
  Then update the CSS variable:
  ```css
  --font-primary: 'Roboto', sans-serif;
  ```

### Step 3: Add Your Images

1. Create an `images/` folder in your website directory
2. Add your images with these recommended names:
   - `profile.jpg` - Your professional headshot (square, at least 500x500px)
   - `project1.jpg`, `project2.jpg`, etc. - Project screenshots (1200x800px recommended)

**Image Optimization Tips:**
- Use JPG for photos, PNG for graphics with transparency
- Compress images using [TinyPNG](https://tinypng.com/) or [ImageOptim](https://imageoptim.com/)
- Keep file sizes under 500KB for faster loading

---

## ✏️ Adding Content

### About Section

Find this section in `index.html`:

```html
<section id="about" class="section about-section">
    <div class="about-text">
        <p>
            Write a paragraph or two about yourself...
        </p>
    </div>
</section>
```

Replace the placeholder text with your biography. Include:
- Your background and education
- Current position and institution
- Research interests or professional focus
- What motivates your work

### Projects Section

Each project uses this structure:

```html
<div class="project-card">
    <div class="project-image">
        <img src="images/project1.jpg" alt="Project 1">
    </div>
    <div class="project-content">
        <h3 class="project-title">Project Title 1</h3>
        <p class="project-description">
            Brief description of your project...
        </p>
        <div class="project-tags">
            <span class="tag">Tag1</span>
            <span class="tag">Tag2</span>
        </div>
        <a href="#" class="project-link">Learn More →</a>
    </div>
</div>
```

**To add a new project:**
1. Copy the entire `<div class="project-card">...</div>` block
2. Paste it below the existing projects
3. Update the image, title, description, and tags
4. Change the link to point to your project page or GitHub repo

**To remove a project:**
- Delete the entire `<div class="project-card">...</div>` block

### Publications Section

Each publication follows this format:

```html
<div class="publication-item">
    <div class="publication-year">2024</div>
    <div class="publication-content">
        <h3 class="publication-title">
            Title of Your Publication
        </h3>
        <p class="publication-authors">
            <strong>Your Name</strong>, Co-Author 1, Co-Author 2
        </p>
        <p class="publication-venue">
            <em>Journal/Conference Name</em>, Volume(Issue), Pages
        </p>
        <div class="publication-links">
            <a href="#" class="pub-link">PDF</a>
            <a href="#" class="pub-link">DOI</a>
            <a href="#" class="pub-link">Code</a>
        </div>
    </div>
</div>
```

**Tips:**
- Use `<strong>Your Name</strong>` to bold your name in the author list
- Link to actual PDFs, DOI pages, and GitHub repositories
- Add or remove link buttons as needed
- Sort by year (most recent first)

### Navigation Menu

To add or remove sections from the navigation:

1. Find the `<nav>` section in `index.html`
2. Add/remove menu items:
```html
<li class="nav-item"><a href="#newsection" class="nav-link">New Section</a></li>
```
3. Create a matching section in the HTML:
```html
<section id="newsection" class="section">
    <div class="container">
        <h2 class="section-title">New Section</h2>
        <!-- Your content here -->
    </div>
</section>
```

---

## 📧 Setting Up the Contact Form

The contact form needs to be connected to a service to actually send emails. Here are your options:

### Option 1: Formspree (Easiest - Recommended for Beginners)

1. Go to [Formspree.io](https://formspree.io/) and create a free account
2. Create a new form and get your form endpoint (e.g., `https://formspree.io/f/xvgpqazn`)
3. Open `script.js` and find the contact form section
4. Replace the demo code with:

```javascript
fetch('https://formspree.io/f/YOUR_FORM_ID', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
})
.then(response => response.json())
.then(data => {
    alert('Thank you! Your message has been sent.');
    contactForm.reset();
})
.catch(error => {
    console.error('Error:', error);
    alert('Sorry, there was an error. Please try emailing directly.');
});
```

### Option 2: EmailJS

1. Sign up at [EmailJS.com](https://www.emailjs.com/)
2. Follow their setup guide
3. Use their JavaScript SDK in your `script.js`

### Option 3: Netlify Forms (If hosting on Netlify)

1. Add `netlify` attribute to your form in `index.html`:
```html
<form id="contactForm" name="contact" method="POST" data-netlify="true">
```
2. That's it! Netlify handles the rest automatically.

### Option 4: Simple Mailto Link

If you don't want a form service, you can use a simple email link:

```javascript
const mailtoLink = `mailto:your.email@example.com?subject=Message from ${formData.name}&body=${formData.message}`;
window.location.href = mailtoLink;
```

---

## 🚀 Deploying Your Website

### Option 1: GitHub Pages (Free & Easy)

1. Create a GitHub account at [github.com](https://github.com)
2. Create a new repository named `yourusername.github.io`
3. Upload your website files to the repository
4. Your site will be live at `https://yourusername.github.io`

**Step-by-step:**
```bash
# In your website folder
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/yourusername.github.io.git
git push -u origin main
```

### Option 2: Netlify (Also Free)

1. Go to [netlify.com](https://www.netlify.com/)
2. Sign up with GitHub
3. Click "Add new site" → "Deploy manually"
4. Drag and drop your website folder
5. Your site is live! (You'll get a URL like `random-name.netlify.app`)

**Custom Domain:**
- Netlify lets you change to `yourname.netlify.app` for free
- You can also connect a custom domain you purchase

### Option 3: Vercel

1. Go to [vercel.com](https://vercel.com/)
2. Sign up with GitHub
3. Import your repository
4. Deploy!

---

## 🎨 Advanced Customization

### Changing the Layout

The website uses CSS Grid and Flexbox for layout. Key sections to modify:

**About Section (2-column layout):**
```css
.about-content {
    display: grid;
    grid-template-columns: 1fr 2fr;  /* Change ratio here */
    gap: 3rem;
}
```

**Projects Grid:**
```css
.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    /* Change 320px to adjust card minimum width */
}
```

### Adding Animation

The website includes fade-in animations. To add more:

```css
/* In styles.css */
.your-element {
    animation: fadeInUp 0.8s ease;
}
```

### Adding a Blog Section

1. Create a new section in `index.html`:
```html
<section id="blog" class="section">
    <div class="container">
        <h2 class="section-title">Blog</h2>
        <!-- Add blog posts here -->
    </div>
</section>
```

2. Add styling in `styles.css`:
```css
.blog-post {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid var(--border-color);
}
```

3. Add to navigation menu

### Mobile Responsiveness

The site is already responsive! Test it by:
1. Opening your browser's Developer Tools (F12)
2. Clicking the device icon to toggle device mode
3. Trying different screen sizes

To adjust mobile breakpoints, modify in `styles.css`:
```css
@media (max-width: 768px) {
    /* Mobile styles */
}
```

---

## 🔧 Troubleshooting

### Images Not Showing

- **Check file path:** Make sure `images/profile.jpg` matches your actual filename
- **Case sensitivity:** Use exact filename case (Profile.jpg ≠ profile.jpg)
- **File format:** Ensure images are .jpg, .png, or .webp

### Navigation Not Working

- Check that section IDs match navigation links
- Example: `<a href="#about">` should point to `<section id="about">`

### Styling Not Applying

- Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Check that `styles.css` is in the same folder as `index.html`
- Verify the `<link>` tag in the HTML `<head>`

### Form Not Sending

- Make sure you've configured a form service (see Contact Form section)
- Check browser console for errors (F12 → Console tab)

---

## 📚 Additional Resources

### Learning HTML/CSS/JavaScript
- [MDN Web Docs](https://developer.mozilla.org/) - Comprehensive web development documentation
- [freeCodeCamp](https://www.freecodecamp.org/) - Free coding courses
- [CSS-Tricks](https://css-tricks.com/) - CSS tutorials and guides

### Design Inspiration
- [Dribbble](https://dribbble.com/) - Design inspiration
- [Awwwards](https://www.awwwards.com/) - Award-winning web design
- [Behance](https://www.behance.net/) - Creative portfolios

### Free Stock Images
- [Unsplash](https://unsplash.com/)
- [Pexels](https://www.pexels.com/)
- [Pixabay](https://pixabay.com/)

### Icons
- [Heroicons](https://heroicons.com/) - Free SVG icons
- [Font Awesome](https://fontawesome.com/) - Icon library
- [Feather Icons](https://feathericons.com/) - Simple, clean icons

---

## 🎯 Checklist: Before You Launch

- [ ] Replace all `[Your Name]` placeholders
- [ ] Update email addresses and social media links
- [ ] Add your profile photo to `images/profile.jpg`
- [ ] Write your About section
- [ ] Add at least 3 projects
- [ ] Add your publications (if applicable)
- [ ] Customize colors in CSS variables
- [ ] Test on mobile (use browser dev tools)
- [ ] Set up contact form service
- [ ] Check all links work
- [ ] Optimize and compress images
- [ ] Test in different browsers (Chrome, Firefox, Safari)
- [ ] Add a favicon (optional but nice!)

---

## 💡 Tips for Success

1. **Keep it simple:** Don't add too much content at once. Start with the essentials.
2. **Update regularly:** Add new projects and publications as they happen.
3. **Test thoroughly:** Check your site on different devices and browsers.
4. **Use high-quality images:** Professional photos make a big difference.
5. **Keep loading fast:** Compress images and minimize unnecessary scripts.
6. **Get feedback:** Ask friends or colleagues to review your site.
7. **SEO basics:** Include descriptive alt text for images and a good meta description.

---

## 🆘 Need Help?

If you run into issues:

1. Check the troubleshooting section above
2. Search for your error message on [Stack Overflow](https://stackoverflow.com/)
3. Review the browser console for error messages (F12 → Console)
4. Validate your HTML at [validator.w3.org](https://validator.w3.org/)
5. Validate your CSS at [jigsaw.w3.org/css-validator/](https://jigsaw.w3.org/css-validator/)

---

## 🎉 You're All Set!

Your website is ready to customize and deploy. Remember, your personal website is a living document – update it regularly as you complete new projects and achieve new milestones.

Good luck, and happy coding! 🚀

---

**Last Updated:** January 2026
**Version:** 1.0
