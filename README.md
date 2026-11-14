# AgriVision AI – Frontend Demo (v2)

Frontend-only demo for AgriVision AI (Build Beyond'26, Gradient Club, BMS College of Engineering).
Pure HTML, CSS and JavaScript with Chart.js from CDN. No build step.

## Run
Open `index.html` in a browser, or serve the folder with any static server, e.g. `python -m http.server`.
An internet connection is needed for Chart.js and Google Fonts.

## Demo accounts
- Farmer: ramesh@demo.in / farmer123
- Buyer: buyer@demo.in / buyer123 (FreshMart Wholesale)
- Admin: admin@demo.in / admin123

## Demo flow
1. Log in as the farmer. Open AI quality check, add a produce photo, run Analyze, set the asking price, then publish.
2. Open Price intelligence for the charts and the suggested price.
3. Log out, log in as the buyer, open Explore produce, view a listing and place a bid.
4. Log in as the farmer, open Bids and accept the bid.

## What changed in v2
- **Photos instead of emoji.** Photos are resized and saved with the listing, and shown on cards and detail views. Crops without a photo get a neutral crop tile.
- **New visual system.** A forest-green and wheat palette replaces the default Tailwind greens. Colours, radii and shadows are tokens at the top of `style.css`. Hover lift and count-up animations are removed. Hover effects now appear only on clickable cards.
- **Icons.** Emoji and text glyphs are replaced with one stroke icon set (`ICONS` in `data.js`).
- **Quality check.** Four steps are shown with progress. Analyze is disabled until a photo is added. The result shows a highlight overlay (marked illustrative), an editable asking price, and a clear publish action.
- **Price intelligence.** Crop and market dropdowns keep their selection. The movement figure is calculated from the data (▲ 2.3%, previously a fixed 4.2%). The price range bar is positioned from the values, not by hand. The bar chart and its labels are clearer.
- **Bids.** Choose a listing with a dropdown. Each bid shows its difference from the asking price, and the chart uses a zero baseline. Accept and reject ask for confirmation, and accepting declines the other open bids.
- **Bug fixes.** Withdrawn listings show "Withdrawn" instead of "Pending". Farmers can restore withdrawn listings. Farmers cannot unhide listings that an admin hid. The bids page no longer hardcodes listing L1. The sales table shows the real seller name. User-entered text is escaped everywhere.
- **Dialogs.** Modals have a close button and close on Escape. Destructive actions are confirmed.
- **Accessibility.** Muted text meets WCAG AA contrast. Interactive cards and the drop zone work with the keyboard. Icon-only buttons have labels.
- **Mobile.** The sidebar becomes a bottom tab bar on small screens.
- **Sign-in and registration.** A product panel sits beside the form on desktop. Passwords can be shown or hidden. Registration uses a Karnataka district list and an optional mobile number, validated as 10 digits.

The browser storage key changed to `agrivision-demo-v2`, so earlier demo data is not loaded. Clear it manually only if you want to see the old data.

## Project structure
```
AgriVisionAI/
├── index.html              redirects to login or the user's dashboard
├── login.html
├── register.html
├── farmer/                 dashboard, quality-inspection, price-intelligence, marketplace,
│                           my-produce, bids, sales-history
├── buyer/                  dashboard, explore, my-bids, saved-listings, purchases
├── admin/                  dashboard, users, moderation, activity
└── assets/
    ├── css/style.css       design tokens, components and responsive layout
    ├── js/data.js          config, sample data, icons, routes, load()/save(), helpers
    ├── js/ui.js            auth screens, app shell, views, charts and render()
    └── js/actions.js       button actions, form handlers and page boot
```

## Where to edit
- Colours, type and spacing: `:root` variables at the top of `assets/css/style.css`
- Sample numbers (reference price, suggested price, forecast range, demand): constants at the top of `assets/js/data.js`
- Sample listings and bids: `seed()` in `assets/js/data.js`
- Persistence: `load()` / `save()` in `assets/js/data.js` (localStorage key `agrivision-demo-v2`; clear it to reset)
- Screens: functions in `VIEWS` in `assets/js/ui.js`
- Button behaviour: `act()` in `assets/js/actions.js`
- Icons: `ICONS` in `assets/js/data.js`

## Backend integration (later)
Replace `load()`/`save()` and the `db` mutations in `actions.js` with Django REST calls.
Sample prices, the AI report and the demand figures are illustrative and must be replaced with real model and market data.
Passwords are stored in plain text in this demo. Hash them on the server.

## Not yet done
- Kannada and Hindi translations
- Phone-number login with OTP
- Real model output for crop, grade and highlight regions
