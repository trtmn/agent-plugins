---
name: wp-custom-theme
description: "Use this skill whenever the user is creating, editing, maintaining, or debugging a custom WordPress theme. Trigger for any of the following: building a theme from scratch, modifying theme templates (header.php, footer.php, single.php, page.php, etc.), working with functions.php, registering hooks or filters, styling with theme CSS or theme.json, adding Gutenberg block support, customizing block styles, optimizing theme performance, or reviewing theme security. Also trigger when the user mentions template hierarchy, child themes, enqueuing scripts/styles, custom post types in a theme context, WordPress loop, or WP_Query customizations. If in doubt and WordPress theming is involved, use this skill."
---

# Custom WordPress Theme Skill

A comprehensive guide for creating and maintaining custom WordPress themes at an intermediate level,
covering theme structure, PHP hooks & template tags, CSS/Gutenberg, and performance & security.

-----

## 0. Discovery Interview (Start Here for New Themes)

Before writing any code, interview the user to understand their requirements. Use the answers to
recommend the right theme approach (FSE, Classic, or Hybrid) and tailor the implementation.

### Interview Questions

Ask these questions — you can combine them into a single message, but keep it conversational:

1. **Site type** — What kind of site is this? (blog, portfolio, business/marketing, e-commerce, membership, news/magazine, or other)
2. **Client editing** — Will the site owner / client edit pages and layouts themselves after launch, or is this developer-managed?
3. **Dynamic PHP logic** — Does the theme need complex server-side logic in templates? (e.g. conditional content based on user roles, custom WP_Query loops, real-time data from external APIs)
4. **WordPress version** — What WP version will this run on? (or: is the host keeping WP up to date?)
5. **Existing base** — Starting from scratch, extending an existing theme, or building a child theme?
6. **Plugins** — Any must-have plugins? (WooCommerce, ACF, Elementor, etc. — some conflict with FSE)
7. **Design complexity** — Is this a pixel-perfect custom design, or is an opinionated block-based layout acceptable?

You do not need to ask all seven at once. Start with 1–4; follow up if answers are ambiguous.

### FSE Recommendation Logic

After gathering answers, apply this decision table:

| Signal | Favours |
|---|---|
| Client will edit layouts/pages themselves | **FSE** |
| New project on WP 6.4+ | **FSE** |
| Design-focused, visually rich site | **FSE** |
| No complex PHP needed in templates | **FSE** |
| Complex PHP logic in templates (conditional output, custom queries) | **Classic** |
| Legacy/existing classic theme being extended | **Classic** |
| Page-builder plugin (Elementor, Divi) in use | **Classic** |
| WooCommerce without FSE-compatible theme | **Classic** (or verify plugin FSE support first) |
| Wants block editor design system, but keeps some PHP templates | **Hybrid** |
| Migrating gradually from classic → FSE | **Hybrid** |

**Default recommendation:** If the project is new, WP is current, and no blocking PHP complexity exists → recommend **FSE**. It is the future direction of WordPress and gives clients the best self-editing experience.

### Output After Interview

Summarise your recommendation in one short paragraph before starting the theme, e.g.:

> "Based on your answers, I'll build a **Full Site Editing (FSE) theme**. The client needs to edit
> page layouts themselves, and there's no complex PHP logic required. I'll use block templates in
> `/templates/`, template parts in `/parts/`, and `theme.json` as the design system. No `header.php`
> or `footer.php` needed."

Then proceed to the relevant sections below.

-----

## 1. Theme File Structure & Setup

### Minimum Required Files

```
my-theme/
├── style.css          ← Theme header (name, version, author, etc.)
├── index.php          ← Fallback template
├── functions.php      ← Theme setup, hooks, enqueues
└── screenshot.png     ← 1200×900px theme preview (optional but recommended)
```

### Recommended Full Structure

```
my-theme/
├── style.css
├── index.php
├── functions.php
├── screenshot.png
│
├── templates/         ← Full-page templates (or page-{slug}.php at root)
│   └── template-landing.php
│
├── template-parts/    ← Reusable partials
│   ├── content.php
│   ├── content-single.php
│   └── header/
│       └── site-branding.php
│
├── inc/               ← Modular PHP includes
│   ├── theme-setup.php
│   ├── enqueue.php
│   ├── custom-post-types.php
│   └── block-support.php
│
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
│
├── header.php
├── footer.php
├── sidebar.php
├── single.php
├── page.php
├── archive.php
├── search.php
├── 404.php
└── theme.json         ← Block editor settings (FSE / hybrid themes)
```

### style.css Header

```css
/*
Theme Name:   My Custom Theme
Theme URI:    https://example.com/my-theme
Author:       Your Name
Author URI:   https://example.com
Description:  A custom theme for...
Version:      1.0.0
Requires at least: 6.5
Tested up to: 6.7
Requires PHP: 8.1
License:      GPL-2.0-or-later
Text Domain:  my-custom-theme
*/
```

### Child Theme Setup

Child themes are the safe way to extend an existing theme:

```css
/* child/style.css */
/*
Theme Name:  My Child Theme
Template:    parent-theme-folder-name
Version:     1.0.0
*/
```

```php
// child/functions.php
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style(
        'parent-style',
        get_template_directory_uri() . '/style.css'
    );
    wp_enqueue_style(
        'child-style',
        get_stylesheet_uri(),
        [ 'parent-style' ]
    );
});
```

-----

## 2. PHP: Theme Setup, Template Tags & Hooks

### Core Theme Setup (functions.php or inc/theme-setup.php)

```php
add_action( 'after_setup_theme', function() {
    // Translations
    load_theme_textdomain( 'my-custom-theme', get_template_directory() . '/languages' );

    // HTML5 support
    add_theme_support( 'html5', [ 'search-form', 'comment-form', 'gallery', 'caption' ] );

    // Title tag (never hardcode <title> in header.php)
    add_theme_support( 'title-tag' );

    // Post thumbnails
    add_theme_support( 'post-thumbnails' );
    add_image_size( 'hero', 1920, 600, true );

    // Custom logo
    add_theme_support( 'custom-logo', [
        'width'       => 250,
        'height'      => 80,
        'flex-width'  => true,
        'flex-height' => true,
    ]);

    // Register nav menus
    register_nav_menus([
        'primary' => __( 'Primary Menu', 'my-custom-theme' ),
        'footer'  => __( 'Footer Menu', 'my-custom-theme' ),
    ]);

    // Woocommerce support (if applicable)
    // add_theme_support( 'woocommerce' );
});
```

### Enqueueing Scripts & Styles (always use wp_enqueue, never hardcode)

```php
add_action( 'wp_enqueue_scripts', function() {
    $ver = wp_get_theme()->get( 'Version' );

    wp_enqueue_style( 'my-theme-style', get_stylesheet_uri(), [], $ver );

    // Enqueue only where needed
    if ( is_singular() && comments_open() ) {
        wp_enqueue_script( 'comment-reply' );
    }

    wp_enqueue_script(
        'my-theme-main',
        get_template_directory_uri() . '/assets/js/main.js',
        [],
        $ver,
        true  // load in footer
    );

    // Pass data to JS (WP 6.5+: prefer wp_add_inline_script over wp_localize_script)
    wp_add_inline_script(
        'my-theme-main',
        'window.myTheme = ' . wp_json_encode([
            'ajaxUrl' => admin_url( 'admin-ajax.php' ),
            'nonce'   => wp_create_nonce( 'my_theme_nonce' ),
        ]),
        'before'
    );
});
```

### Essential Template Tags

```php
// In templates
get_header();            // Loads header.php
get_footer();            // Loads footer.php
get_sidebar();           // Loads sidebar.php
get_template_part( 'template-parts/content', get_post_type() );

// URLs & paths (always use these, never hardcode)
get_template_directory_uri()    // URL  — for assets
get_template_directory()        // PATH — for file includes
get_stylesheet_directory_uri()  // Child theme URL
get_stylesheet_directory()      // Child theme path

// Content output
the_title();
the_content();
the_excerpt();
the_post_thumbnail( 'hero' );
the_permalink();
the_author_posts_link();
the_date( 'F j, Y' );
```

### The Loop

```php
if ( have_posts() ) :
    while ( have_posts() ) : the_post();
        get_template_part( 'template-parts/content', get_post_format() );
    endwhile;
    the_posts_pagination();
else :
    get_template_part( 'template-parts/content', 'none' );
endif;
```

### Custom Query (use sparingly; prefer pre_get_posts for main query)

```php
// Modify main query — preferred approach
add_action( 'pre_get_posts', function( WP_Query $query ) {
    if ( ! is_admin() && $query->is_main_query() && $query->is_category() ) {
        $query->set( 'posts_per_page', 12 );
    }
});

// Secondary query — when you truly need a second loop
$args  = [ 'post_type' => 'project', 'posts_per_page' => 6 ];
$query = new WP_Query( $args );
if ( $query->have_posts() ) :
    while ( $query->have_posts() ) : $query->the_post();
        // output
    endwhile;
    wp_reset_postdata(); // ← always reset!
endif;
```

### Useful Hooks Cheat Sheet

|Hook                      |Type  |Use                        |
|--------------------------|------|---------------------------|
|`after_setup_theme`       |action|Theme supports, menus      |
|`wp_enqueue_scripts`      |action|CSS/JS                     |
|`pre_get_posts`           |action|Modify main query          |
|`the_content`             |filter|Modify post content        |
|`body_class`              |filter|Add custom body classes    |
|`nav_menu_link_attributes`|filter|Add attrs to menu links    |
|`excerpt_length`          |filter|Control auto-excerpt length|
|`upload_mimes`            |filter|Allow extra file types     |

-----

## 3. CSS / Styling & Gutenberg Block Support

### theme.json (Block Editor Configuration)

`theme.json` is the modern way to configure editor styles, typography, colors, and spacing:

```json
{
    "$schema": "https://schemas.wp.org/wp/6.6/theme.json",
    "version": 3,
    "settings": {
        "color": {
            "palette": [
                { "name": "Primary",   "slug": "primary",   "color": "#0a66c2" },
                { "name": "Secondary", "slug": "secondary", "color": "#f4f4f4" },
                { "name": "Dark",      "slug": "dark",      "color": "#1a1a1a" }
            ],
            "custom": false,
            "customGradient": false
        },
        "shadow": {
            "presets": [
                { "name": "Small",  "slug": "sm",  "shadow": "0 1px 3px rgba(0,0,0,.12)" },
                { "name": "Medium", "slug": "md",  "shadow": "0 4px 16px rgba(0,0,0,.12)" }
            ],
            "defaultPresets": false
        },
        "typography": {
            "fontFamilies": [
                {
                    "fontFamily": "Inter, sans-serif",
                    "name": "Inter",
                    "slug": "inter",
                    "fontFace": [
                        {
                            "fontFamily": "Inter",
                            "fontWeight": "400 700",
                            "fontStyle": "normal",
                            "src": [ "file:./assets/fonts/inter.woff2" ]
                        }
                    ]
                }
            ],
            "fluid": true,
            "customFontSize": false
        },
        "spacing": {
            "spacingSizes": [
                { "name": "Small",  "slug": "sm",  "size": "clamp(1rem, 2vw, 1.5rem)" },
                { "name": "Medium", "slug": "md",  "size": "clamp(2rem, 4vw, 3rem)" },
                { "name": "Large",  "slug": "lg",  "size": "clamp(3rem, 6vw, 5rem)" }
            ]
        },
        "layout": {
            "contentSize": "780px",
            "wideSize": "1200px"
        }
    },
    "styles": {
        "typography": {
            "fontFamily": "var(--wp--preset--font-family--inter)",
            "fontSize": "1rem",
            "lineHeight": "1.6"
        },
        "elements": {
            "link": {
                "color": { "text": "var(--wp--preset--color--primary)" },
                ":hover": { "color": { "text": "var(--wp--preset--color--dark)" } }
            }
        }
    }
}
```

### Enabling Block Editor Support in functions.php

```php
add_action( 'after_setup_theme', function() {
    // Load editor styles in Gutenberg
    add_theme_support( 'editor-styles' );
    add_editor_style( 'assets/css/editor.css' );

    // Disable custom colors / font sizes (enforce design system)
    add_theme_support( 'disable-custom-colors' );
    add_theme_support( 'disable-custom-font-sizes' );

    // Wide & full-width alignment
    add_theme_support( 'align-wide' );

    // Block-based widgets (WP 5.8+)
    add_theme_support( 'widgets-block-editor' );
});
```

### Registering Custom Block Styles

```php
add_action( 'init', function() {
    register_block_style( 'core/button', [
        'name'  => 'outline',
        'label' => __( 'Outline', 'my-custom-theme' ),
    ]);

    register_block_style( 'core/group', [
        'name'  => 'card',
        'label' => __( 'Card', 'my-custom-theme' ),
    ]);
});
```

Then style them in CSS:

```css
.wp-block-button.is-style-outline .wp-block-button__link {
    background: transparent;
    border: 2px solid currentColor;
}

.wp-block-group.is-style-card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,.08);
    padding: var(--wp--preset--spacing--md);
}
```

### Block Patterns

```php
add_action( 'init', function() {
    register_block_pattern(
        'my-theme/hero-section',
        [
            'title'       => __( 'Hero Section', 'my-custom-theme' ),
            'categories'  => [ 'featured' ],
            'content'     => '<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"var(--wp--preset--spacing--lg)","bottom":"var(--wp--preset--spacing--lg)"}}}} --><div class="wp-block-group alignfull"><!-- wp:heading {"level":1} --><h1>Welcome to My Site</h1><!-- /wp:heading --></div><!-- /wp:group -->',
        ]
    );
});
```

### Responsive CSS Conventions

```css
/* Use CSS custom properties that align with theme.json */
:root {
    --color-primary: var(--wp--preset--color--primary, #0a66c2);
    --spacing-md: var(--wp--preset--spacing--md, 2rem);
}

/* Prefer logical properties */
.entry-content {
    margin-block: var(--spacing-md);
    padding-inline: 1rem;
}

/* Fluid typography without theme.json */
h1 { font-size: clamp(2rem, 5vw, 3.5rem); }
```

-----

## 4. Performance & Security Best Practices

### Performance

**Script / Style loading**

- Always set `$in_footer = true` for non-critical scripts
- Use `wp_add_inline_style()` for small critical CSS overrides
- Avoid `@import` in CSS — use `wp_enqueue_style` dependencies instead
- Conditionally enqueue assets: `if ( is_page_template('templates/contact.php') ) { ... }`

**Images**

```php
// Lazy-load images below the fold
add_filter( 'wp_lazy_loading_enabled', '__return_true' );

// Add loading="eager" to LCP image (hero)
add_filter( 'wp_get_attachment_image_attributes', function( $attr, $attachment, $size ) {
    if ( $size === 'hero' ) {
        $attr['loading']   = 'eager';
        $attr['fetchpriority'] = 'high';
    }
    return $attr;
}, 10, 3 );
```

**Queries**

- Use `pre_get_posts` instead of secondary `WP_Query` for the main loop
- Cache expensive queries with WordPress Transients:

```php
$data = get_transient( 'my_theme_featured_posts' );
if ( false === $data ) {
    $data = new WP_Query([ 'post_type' => 'post', 'posts_per_page' => 3 ]);
    set_transient( 'my_theme_featured_posts', $data, HOUR_IN_SECONDS );
}
```

**Template loading**

- Use `get_template_part()` — it’s cached by WordPress
- Avoid `require`/`include` for template parts

-----

### Security

**Output escaping — always escape late, escape on output**

```php
// ❌ Don't do this
echo get_the_title();

// ✅ Do this
echo esc_html( get_the_title() );
echo esc_url( get_permalink() );
echo esc_attr( $custom_field_value );
echo wp_kses_post( $html_content );  // allows safe HTML tags
```

**Nonces for forms and AJAX**

```php
// In template
wp_nonce_field( 'my_form_action', 'my_nonce' );

// On form submission / AJAX handler
if ( ! isset( $_POST['my_nonce'] ) || ! wp_verify_nonce( $_POST['my_nonce'], 'my_form_action' ) ) {
    wp_die( 'Security check failed.' );
}
```

**Input sanitization**

```php
$name  = sanitize_text_field( $_POST['name'] ?? '' );
$email = sanitize_email( $_POST['email'] ?? '' );
$url   = esc_url_raw( $_POST['url'] ?? '' );
$int   = absint( $_GET['page'] ?? 0 );
```

**Capabilities and user roles**

```php
if ( ! current_user_can( 'edit_posts' ) ) {
    wp_die( __( 'Sorry, you are not allowed to do that.', 'my-custom-theme' ) );
}
```

**Hide WordPress version & login hints**

```php
// Remove WP version from head
remove_action( 'wp_head', 'wp_generator' );

// Neutralize login error messages
add_filter( 'login_errors', fn() => __( 'Invalid credentials.', 'my-custom-theme' ) );

// Disable XML-RPC if not needed
add_filter( 'xmlrpc_enabled', '__return_false' );
```

**Disable file editing from admin**
Add to `wp-config.php` (not the theme, but remind clients):

```php
define( 'DISALLOW_FILE_EDIT', true );
```

-----

## 5. Template Hierarchy Quick Reference

WordPress resolves templates in this order (most specific → least specific):

|Context        |Template lookup order                                                                            |
|---------------|-------------------------------------------------------------------------------------------------|
|Single post    |`single-{type}-{slug}.php` → `single-{type}.php` → `single.php` → `singular.php` → `index.php`   |
|Page           |`{slug}.php` → `page-{id}.php` → `page.php` → `singular.php` → `index.php`                       |
|Category       |`category-{slug}.php` → `category-{id}.php` → `category.php` → `archive.php` → `index.php`       |
|Custom taxonomy|`taxonomy-{tax}-{term}.php` → `taxonomy-{tax}.php` → `taxonomy.php` → `archive.php` → `index.php`|
|Search         |`search.php` → `index.php`                                                                       |
|404            |`404.php` → `index.php`                                                                          |

Full reference: https://developer.wordpress.org/themes/basics/template-hierarchy/

-----

## 6. Full Site Editing (FSE)

FSE themes replace PHP template files with block-based HTML templates, making the entire site
(header, footer, sidebar, archives, etc.) editable from **Appearance → Editor** in wp-admin.
They are the future direction of WordPress theming.

### FSE vs Classic vs Hybrid — When to Use Each

|Approach                                          |When to choose                                                           |
|--------------------------------------------------|-------------------------------------------------------------------------|
|**Classic theme** (PHP templates)                 |Complex PHP logic, heavily customised queries, legacy projects           |
|**Hybrid theme** (PHP + theme.json + block styles)|Gradual migration; block editor design system without full FSE commitment|
|**Full FSE theme** (block templates only)         |New projects, design-focused sites, client self-editing, future-proofing |

-----

### FSE Theme File Structure

```
my-fse-theme/
├── style.css              ← Theme header (same as classic)
├── theme.json             ← Design system (colors, fonts, spacing, layout)
├── functions.php          ← Minimal — enqueues, block styles, patterns
│
├── templates/             ← Full-page block templates (replaces *.php files)
│   ├── index.html         ← Required fallback
│   ├── single.html
│   ├── page.html
│   ├── archive.html
│   ├── search.html
│   └── 404.html
│
├── parts/                 ← Reusable template parts (replaces header.php etc.)
│   ├── header.html
│   ├── footer.html
│   └── sidebar.html
│
├── patterns/              ← Registered block patterns (.php files)
│   └── hero-section.php
│
└── assets/
    ├── css/
    ├── js/
    └── fonts/
```

Declare FSE support in `style.css` by adding:

```css
/*
...
Template:
*/
```

And in `functions.php`:

```php
add_action( 'after_setup_theme', function() {
    add_theme_support( 'block-templates' ); // Enables FSE
});
```

-----

### Block Templates

Templates live in `/templates/` as `.html` files containing serialized block markup.
WordPress still follows the **template hierarchy** — it just looks for `.html` files instead of `.php`.

A minimal `templates/index.html`:

```html
<!-- wp:template-part {"slug":"header","tagName":"header"} /-->

<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->
<main class="wp-block-group">

    <!-- wp:query {"queryId":0,"query":{"perPage":10,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","inherit":true}} -->
    <div class="wp-block-query">

        <!-- wp:post-template -->
            <!-- wp:post-title {"isLink":true} /-->
            <!-- wp:post-excerpt /-->
            <!-- wp:post-date /-->
        <!-- /wp:post-template -->

        <!-- wp:query-pagination -->
            <!-- wp:query-pagination-previous /-->
            <!-- wp:query-pagination-numbers /-->
            <!-- wp:query-pagination-next /-->
        <!-- /wp:query-pagination -->

    </div>
    <!-- /wp:query -->

</main>
<!-- /wp:group -->

<!-- wp:template-part {"slug":"footer","tagName":"footer"} /-->
```

A minimal `parts/header.html`:

```html
<!-- wp:group {"tagName":"header","className":"site-header","layout":{"type":"flex","justifyContent":"space-between"}} -->
<header class="wp-block-group site-header">

    <!-- wp:site-title /-->

    <!-- wp:navigation {"ref":null,"layout":{"type":"flex","justifyContent":"right"}} /-->

</header>
<!-- /wp:group -->
```

> **Tip:** The easiest way to author templates is to build them visually in the Site Editor,
> then copy the block markup from *Editor → (template) → Code Editor* into your theme files.

-----

### theme.json (Extended for FSE)

In FSE themes, `theme.json` fully replaces the Customizer and most of `functions.php` setup.

```json
{
    "$schema": "https://schemas.wp.org/wp/6.6/theme.json",
    "version": 3,
    "settings": {
        "appearanceTools": true,
        "color": {
            "palette": [
                { "name": "Primary",    "slug": "primary",    "color": "#0a66c2" },
                { "name": "Secondary",  "slug": "secondary",  "color": "#f4f4f4" },
                { "name": "Dark",       "slug": "dark",       "color": "#1a1a1a" },
                { "name": "Light",      "slug": "light",      "color": "#ffffff" }
            ],
            "custom": false,
            "customGradient": false,
            "defaultPalette": false
        },
        "typography": {
            "fontFamilies": [
                {
                    "fontFamily": "Inter, sans-serif",
                    "name": "Inter",
                    "slug": "inter",
                    "fontFace": [
                        {
                            "fontFamily": "Inter",
                            "fontWeight": "400 700",
                            "fontStyle": "normal",
                            "src": [ "file:./assets/fonts/inter.woff2" ]
                        }
                    ]
                }
            ],
            "fontSizes": [
                { "name": "Small",   "slug": "sm",   "size": "clamp(0.875rem, 1.5vw, 1rem)" },
                { "name": "Base",    "slug": "base", "size": "clamp(1rem, 2vw, 1.125rem)" },
                { "name": "Large",   "slug": "lg",   "size": "clamp(1.25rem, 3vw, 1.75rem)" },
                { "name": "XLarge",  "slug": "xl",   "size": "clamp(1.75rem, 5vw, 3rem)" }
            ],
            "fluid": true,
            "customFontSize": false,
            "defaultFontSizes": false
        },
        "spacing": {
            "spacingSizes": [
                { "name": "XSmall", "slug": "xs", "size": "0.5rem" },
                { "name": "Small",  "slug": "sm", "size": "clamp(1rem, 2vw, 1.5rem)" },
                { "name": "Medium", "slug": "md", "size": "clamp(2rem, 4vw, 3rem)" },
                { "name": "Large",  "slug": "lg", "size": "clamp(3rem, 6vw, 5rem)" }
            ],
            "units": [ "px", "rem", "em", "%" ],
            "customSpacingSize": false,
            "defaultSpacingSizes": false
        },
        "layout": {
            "contentSize": "780px",
            "wideSize": "1200px"
        },
        "blocks": {
            "core/button": {
                "color": { "custom": false }
            }
        }
    },
    "styles": {
        "color": {
            "background": "var(--wp--preset--color--light)",
            "text": "var(--wp--preset--color--dark)"
        },
        "typography": {
            "fontFamily": "var(--wp--preset--font-family--inter)",
            "fontSize": "var(--wp--preset--font-size--base)",
            "lineHeight": "1.6"
        },
        "spacing": {
            "blockGap": "var(--wp--preset--spacing--md)"
        },
        "elements": {
            "link": {
                "color": { "text": "var(--wp--preset--color--primary)" },
                ":hover": { "color": { "text": "var(--wp--preset--color--dark)" } }
            },
            "h1": { "typography": { "fontSize": "var(--wp--preset--font-size--xl)", "lineHeight": "1.15" } },
            "h2": { "typography": { "fontSize": "var(--wp--preset--font-size--lg)", "lineHeight": "1.2" } }
        },
        "blocks": {
            "core/navigation": {
                "typography": { "fontSize": "var(--wp--preset--font-size--sm)" }
            }
        }
    }
}
```

**Key `theme.json` v3 properties to know:**

- `"appearanceTools": true` — unlocks border, padding, margin, link color controls per-block in the editor
- `"defaultPalette": false` — hides WordPress's built-in color palette (enforces your design system)
- `"defaultPresets": false` on shadow — hides WP's built-in shadow presets (v3+)
- `styles.blocks` — apply default styles to specific core blocks globally
- `settings.blocks` — restrict or expand settings per block type
- **Version 3 requires WordPress 6.6+.** For sites on 6.5 or below, use version 2.

-----

### Block Patterns in FSE

In FSE themes, patterns are registered via PHP files dropped in the `/patterns/` directory.
WordPress auto-registers them — no `register_block_pattern()` call needed.

`patterns/hero-section.php`:

```php
<?php
/**
 * Title: Hero Section
 * Slug: my-fse-theme/hero-section
 * Categories: featured, banner
 * Keywords: hero, banner, intro
 * Viewport Width: 1280
 */
?>
<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"var:preset|spacing|lg","bottom":"var:preset|spacing|lg"}}},"backgroundColor":"primary","textColor":"light","layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull has-primary-background-color has-light-color has-background has-text-color">

    <!-- wp:heading {"level":1,"textAlign":"center"} -->
    <h1 class="wp-block-heading has-text-align-center">Your Headline Here</h1>
    <!-- /wp:heading -->

    <!-- wp:paragraph {"align":"center"} -->
    <p class="has-text-align-center">A compelling subheading that supports your headline.</p>
    <!-- /wp:paragraph -->

    <!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
    <div class="wp-block-buttons">
        <!-- wp:button -->
        <div class="wp-block-button"><a class="wp-block-button__link wp-element-button">Get Started</a></div>
        <!-- /wp:button -->
    </div>
    <!-- /wp:buttons -->

</div>
<!-- /wp:group -->
```

-----

### Styling FSE Themes

Since FSE themes use `theme.json` as the design token source, reference those tokens in your CSS
rather than hardcoding values:

```css
/* assets/css/style.css */

/* Use generated CSS custom properties from theme.json */
.site-header {
    background-color: var(--wp--preset--color--light);
    border-block-end: 1px solid rgba(0,0,0,.08);
    position: sticky;
    top: 0;
    z-index: 100;
}

/* Block-specific overrides */
.wp-block-post-title a {
    color: var(--wp--preset--color--dark);
    text-decoration: none;
}

.wp-block-post-title a:hover {
    color: var(--wp--preset--color--primary);
}

/* Responsive layout helpers */
@media (max-width: 600px) {
    .site-header {
        position: relative; /* disable sticky on mobile if needed */
    }
}
```

Enqueue the stylesheet the normal way in `functions.php` — it applies to both frontend and
(via `add_editor_style`) the Site Editor:

```php
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style( 'my-fse-theme', get_stylesheet_uri(), [], wp_get_theme()->get('Version') );
});

add_action( 'after_setup_theme', function() {
    add_theme_support( 'editor-styles' );
    add_editor_style( 'style.css' );
});
```

-----

### Block Hooks (WP 6.4+)

Block Hooks let you inject blocks into specific positions in templates — without editing template files:

```php
add_filter( 'hooked_block_types', function( array $hooked_blocks, string $position, string $anchor_block ) : array {
    if ( 'core/template-part' === $anchor_block && 'after' === $position ) {
        $hooked_blocks[] = 'my-theme/announcement-bar';
    }
    return $hooked_blocks;
}, 10, 3 );
```

Or declaratively in `block.json` for custom blocks:

```json
{
    "blockHooks": {
        "core/post-content": "before"
    }
}
```

-----

### Style Variations (FSE)

Drop alternate `theme.json` files in a `styles/` directory — users can switch between them via *Appearance → Editor → Styles*:

```
my-fse-theme/
└── styles/
    ├── dark.json       ← overrides colors, backgrounds
    └── high-contrast.json
```

`styles/dark.json` only needs to declare what differs from `theme.json`:

```json
{
    "$schema": "https://schemas.wp.org/wp/6.6/theme.json",
    "version": 3,
    "title": "Dark",
    "styles": {
        "color": {
            "background": "var(--wp--preset--color--dark)",
            "text": "var(--wp--preset--color--light)"
        }
    }
}
```

-----

### FSE Limitations & Gotchas

- **No PHP in templates** — block templates are pure HTML/block markup. For dynamic output, use a custom block or a Server-Side Rendered (SSR) block via `register_block_type()`.
- **Template locking** — use `"templateLock": "all"` or `"contentOnly"` in block markup to restrict what clients can edit.
- **Navigation block** — requires a saved Navigation post in the database; can be tricky in fresh installs. Export/import with `theme.json` patterns where possible.
- **Avoid over-relying on the visual editor** for complex layouts; always version-control the resulting `.html` files — they are source of truth, not the database.
- **theme.json version** — version 3 (WP 6.6+) is the current standard; version 2 themes still work but miss shadow presets, improved CSS variable output, and other enhancements.
- **Font Library (WP 6.5+)** — users can install fonts directly from the editor (*Appearance → Editor → Styles → Typography*). Theme-bundled fonts in `theme.json` `fontFace` still take precedence; keep both in sync.

-----

## 7. Modern APIs (WP 6.4 – 6.7)

### Interactivity API (WP 6.4+)

The Interactivity API replaces ad-hoc `<script>` tags and jQuery for frontend interactivity in blocks. It uses declarative HTML directives backed by a reactive store.

**Register a block with Interactivity API support:**

```php
// In your block's block.json
{
    "name": "my-theme/accordion",
    "supports": {
        "interactivity": true
    }
}
```

**In the block's render template (render.php):**

```php
wp_interactivity_state( 'my-theme/accordion', [
    'open' => false,
] );
?>
<div
    <?php echo get_block_wrapper_attributes(); ?>
    data-wp-interactive="my-theme/accordion"
>
    <button data-wp-on--click="actions.toggle">
        <?php echo esc_html( $attributes['title'] ); ?>
    </button>
    <div data-wp-bind--hidden="!state.open">
        <?php echo wp_kses_post( $content ); ?>
    </div>
</div>
```

**In `assets/js/accordion.js` (compiled via `@wordpress/scripts`):**

```js
import { store, getContext } from '@wordpress/interactivity';

store( 'my-theme/accordion', {
    actions: {
        toggle() {
            const state = getContext();
            state.open = ! state.open;
        },
    },
} );
```

> Use the Interactivity API for any theme block that requires client-side state (tabs, accordions, modals, menus). For simple one-off effects not tied to a block, vanilla JS with `wp_enqueue_script` is still fine.

-----

### Block Bindings API (WP 6.5+)

Block Bindings connect block attributes to dynamic data sources (post meta, user meta, patterns) without writing a custom block. Available in the editor and on the frontend.

**Register a custom binding source:**

```php
add_action( 'init', function() {
    register_block_bindings_source( 'my-theme/post-meta', [
        'label'              => __( 'Post Meta', 'my-custom-theme' ),
        'get_value_callback' => function( array $source_args ) : mixed {
            return get_post_meta(
                get_the_ID(),
                sanitize_key( $source_args['key'] ?? '' ),
                true
            );
        },
        'uses_context'       => [ 'postId', 'postType' ],
    ] );
} );
```

**Use in a block template or pattern (block comment markup):**

```html
<!-- wp:paragraph {
    "metadata": {
        "bindings": {
            "content": {
                "source": "core/post-meta",
                "args": { "key": "subtitle" }
            }
        }
    }
} -->
<p></p>
<!-- /wp:paragraph -->
```

Built-in sources: `core/post-meta`, `core/user-meta`, `core/taxonomy`, `core/pattern-overrides`.

-----

## 8. Maintenance Checklist

When maintaining an existing theme, systematically check:

- [ ] Theme passes Theme Check plugin (if going to WP.org repo)
- [ ] No PHP errors/warnings (`WP_DEBUG true` in dev); tested on PHP 8.1+
- [ ] All outputs escaped correctly
- [ ] All inputs sanitized & nonces verified
- [ ] Scripts/styles properly enqueued (not hardcoded in templates)
- [ ] `wp_add_inline_script` used instead of `wp_localize_script` for passing data to JS
- [ ] `wp_reset_postdata()` called after every custom `WP_Query`
- [ ] Translation functions used on user-facing strings (`__()`, `esc_html__()`, `_e()`)
- [ ] `theme.json` (version 3 for WP 6.6+) and editor styles keep block editor in sync with frontend
- [ ] Images use `wp_get_attachment_image()` (not manual `<img>` tags with hardcoded URLs)
- [ ] Performance: conditional asset loading, transients for expensive queries
- [ ] No plugin territory code in theme (custom post types people rely on should be in plugins)
- [ ] **FSE-specific:**
  - [ ] Block templates version-controlled (`.html` files are source of truth, not the database)
  - [ ] `theme.json` tokens used in CSS (`var(--wp--preset--color--*)`) — no hardcoded values
  - [ ] Patterns in `/patterns/` folder (not only registered via `register_block_pattern()`)
  - [ ] `add_editor_style()` called so Site Editor matches frontend
  - [ ] Navigation block references a real saved Navigation post (check after fresh install)
  - [ ] Style variations in `styles/` folder tested in Site Editor
  - [ ] Block Hooks used instead of hardcoded template edits where possible
  - [ ] Interactivity API used for blocks with client-side state (no ad-hoc inline `<script>` tags)