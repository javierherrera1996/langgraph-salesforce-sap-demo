# 🎨 Frontend Development Prompt - Belden AI Sales Agent

**Copy and paste this complete prompt to a frontend expert agent (Claude, GPT-4, etc.)**

---

## PROMPT COMPLETO

```
You are an expert frontend developer specializing in AI/ML interfaces. 
I need you to create a modern, professional web interface for an enterprise AI agent.

## 📋 PROJECT CONTEXT

We have developed an **AI Agent for Belden** (industrial network solutions company) 
that automates two sales operations processes:

1. **Lead Qualification**: Qualifies leads from Salesforce and routes them to the correct sales rep
2. **Complaint Classification**: Classifies customer complaints/tickets as Product issues or IT/Services issues and routes them accordingly

The agent is deployed on **Google Cloud Vertex AI Agent Engine** and exposes a REST API.

## 🔌 API BACKEND

### Base URL Options

**Option 1: Local Development**
```
http://localhost:8000
```

**Option 2: Vertex AI Agent Engine (Production)**
```
https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/reasoningEngines/{ENGINE_ID}:query
```

**Option 3: FastAPI Server (if deployed separately)**
```
https://your-api-domain.com
```

### Authentication

For Vertex AI, you need a Bearer token:
```bash
gcloud auth print-access-token
```

For local development, no authentication needed.

---

## 📡 API ENDPOINTS

### 1. Lead Qualification

**Endpoint**: `POST /run/lead`

**Request**:
```json
{
  "lead_data": {
    "Id": "test-lead-001",
    "Company": "TechCorp Industries",
    "FirstName": "Jane",
    "LastName": "Smith",
    "Title": "Chief Technology Officer",
    "Email": "jane.smith@techcorp.com",
    "Phone": "+1-555-0100",
    "Industry": "Technology",
    "Rating": "Hot",
    "AnnualRevenue": 50000000,
    "NumberOfEmployees": 5000,
    "LeadSource": "Partner Referral",
    "Description": "We are expanding our manufacturing facilities and need industrial network infrastructure. Budget approved for Q2 2024. Looking for switches, cables, and network management solutions."
  },
  "use_llm": true
}
```

**Response**:
```json
{
  "workflow": "lead_qualification",
  "status": "completed",
  "result": {
    "score": 0.85,
    "priority": "P1",
    "routing": {
      "owner_type": "AE",
      "priority": "P1",
      "reason": "High-value enterprise lead with C-level decision maker, Hot rating, and Partner Referral source. Budget approved and clear project timeline."
    },
    "reasoning": "[VERDICT: P1] This lead scores 0.85 calculated as:\n1. TITLE: Chief Technology Officer = 0.30 points\n2. COMPANY SIZE: 5000 employees, $50000000 revenue = 0.25 points\n3. INDUSTRY: Technology = 0.15 points\n4. BUYING SIGNALS: Rating=Hot (0.10), Source=Partner Referral (0.08), Description keywords=budget, timeline, project (0.06) = 0.24 total\n5. SAP BONUS: N/A = 0.00 points\nTOTAL: 0.94 points → Final Score: 0.85\nCONCLUSION: Immediate Account Executive engagement recommended",
    "confidence": 0.92,
    "key_factors": [
      "C-level title (CTO)",
      "Enterprise company (5000 employees)",
      "Hot rating",
      "Partner Referral source",
      "Budget approved in description"
    ],
    "recommended_action": "Schedule discovery call within 24 hours. Focus on industrial network infrastructure needs across multiple facilities.",
    "llm_analysis": {
      "model_used": "gpt-4o-mini",
      "reasoning": "...",
      "confidence": 0.92
    },
    "enriched": {
      "business_partner_id": "BP123456",
      "total_orders": 15,
      "total_revenue": 2500000.00,
      "credit_rating": "A",
      "last_order_date": "2024-01-15"
    },
    "actions_done": [
      "fetch_lead",
      "enrich_lead",
      "score_lead",
      "decide_routing",
      "execute_actions",
      "email:lead_alert_sales_agent:sales@belden.com"
    ]
  },
  "execution_time_seconds": 3.45,
  "timestamp": "2024-01-23T19:00:00Z"
}
```

**Key Points**:
- Score >= 0.60 → Email sent to `SALES_AGENT_EMAIL`
- Score determines routing: P1 (≥0.75) → AE, P2 (0.45-0.74) → SDR, P3 (<0.45) → Nurture
- `reasoning` shows step-by-step calculation (CRITICAL to display prominently)
- `enriched` contains SAP business context (if available)

---

### 2. Complaint Classification

**Endpoint**: `POST /run/ticket`

**Request**:
```json
{
  "case_data": {
    "Id": "test-case-001",
    "CaseNumber": "00001234",
    "Subject": "Hirschmann Switch Keeps Restarting",
    "Description": "Our Hirschmann industrial switch has been restarting every 2-3 hours for the past week. This is affecting our production line. The switch is model RS20-0800T1T1SDAEHC. This is urgent.",
    "Priority": "High",
    "Origin": "Web"
  },
  "use_llm": true
}
```

**Response**:
```json
{
  "workflow": "complaint_classification",
  "status": "completed",
  "result": {
    "classification": {
      "is_product_complaint": true,
      "is_it_support": false,
      "product_category": "switches",
      "product_name": "Hirschmann RS20-0800T1T1SDAEHC",
      "confidence": 0.95,
      "reasoning": "This is clearly a product complaint about a Belden switch. The description mentions a specific Hirschmann switch model (RS20-0800T1T1SDAEHC) that is malfunctioning. The issue is affecting production, indicating urgency. This should be routed to the Product Expert team for technical support.",
      "sentiment": "frustrated",
      "urgency": "high",
      "complaint_summary": "Hirschmann switch restarting every 2-3 hours, affecting production",
      "suggested_response": "Thank you for reporting this issue. We understand the urgency as it's affecting your production line. Our Product Expert team will contact you within 2 hours to investigate the switch model RS20-0800T1T1SDAEHC. In the meantime, please check the power supply and ensure proper ventilation around the switch."
    },
    "decision": {
      "action": "email_product_expert",
      "recipient_email": "productos@belden.com",
      "message": "Product complaint (switches) detected. Sending email to Product Expert.",
      "redirect_url": ""
    },
    "actions_done": [
      "fetch_ticket",
      "classify_complaint",
      "decide_action",
      "execute_actions",
      "email:email_product_expert:productos@belden.com",
      "sf:post_comment"
    ]
  },
  "execution_time_seconds": 2.15,
  "timestamp": "2024-01-23T19:00:00Z"
}
```

**Classification Types**:

1. **Product Complaint** (`is_product_complaint: true`)
   - Categories: switches, cables, connectors, software, infrastructure, general
   - Action: `email_product_expert`
   - Recipient: `PRODUCT_EXPERT_EMAIL`
   - Email design: Red theme, product-focused

2. **IT/Services Support** (`is_it_support: true`)
   - Action: `email_services_agent`
   - Recipient: `SERVICES_AGENT_EMAIL`
   - Includes: `redirect_url` to IT support portal
   - Email design: Blue theme, IT-focused

3. **General Inquiry** (neither product nor IT)
   - Default: Routes to `PRODUCT_EXPERT_EMAIL` (default handler)
   - Action: `email_product_expert`

**Key Points**:
- **ALWAYS sends email** with AI analysis (to appropriate recipient)
- Product complaints → Product Expert (red email design)
- IT/Services → Services Agent (blue email design, includes IT portal link)
- `reasoning` explains classification decision (CRITICAL to display)

---

### 3. Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-23T19:00:00Z"
}
```

### 4. Configuration Status

**Endpoint**: `GET /status/config`

**Response**:
```json
{
  "openai": {
    "configured": true,
    "model": "gpt-4o-mini"
  },
  "langsmith": {
    "configured": true,
    "project": "belden-ai-agent"
  },
  "salesforce": {
    "configured": false,
    "mode": "mock"
  },
  "sap": {
    "configured": false,
    "mode": "mock"
  },
  "resend": {
    "configured": true,
    "from_email": "onboarding@resend.dev"
  }
}
```

---

## 🎯 UI REQUIREMENTS

### Main Screens

#### 1. **Dashboard Home**
- Summary metrics:
  - Leads processed today
  - Tickets classified today
  - High-value leads (score >= 0.60)
  - Product complaints vs IT support breakdown
- Quick access cards:
  - "Qualify Lead" button
  - "Classify Complaint" button
- Recent activity feed
- System status indicator (health check)

#### 2. **Lead Qualification Page**

**Form Fields**:
- Company (text input)
- First Name (text input)
- Last Name (text input)
- Title (dropdown with common titles):
  - C-Level (CEO, CTO, CIO, CFO, COO)
  - VP (Vice President, VP Engineering, VP IT)
  - Director (Director of IT, Director Engineering)
  - Manager (IT Manager, Engineering Manager)
  - Other titles
- Email (email input)
- Phone (tel input)
- Industry (dropdown):
  - Technology
  - Financial Services
  - Healthcare
  - Manufacturing
  - Telecommunications
  - Energy/Utilities
  - Logistics/Transportation
  - Retail/Consumer
  - Other
- Rating (radio buttons or slider): Cold / Warm / Hot
- Annual Revenue (number input with formatting)
- Number of Employees (number input)
- Lead Source (dropdown):
  - Partner Referral
  - Event
  - Website
  - Cold Call
  - Other
- Description (textarea, large)

**Result Display** (after API call):
- **Score Display** (large, prominent):
  - Score number (0.00-1.00) in large font
  - Color-coded progress bar:
    - Green (0.75-1.00) = P1 Hot
    - Orange (0.45-0.74) = P2 Warm
    - Red (0.00-0.44) = P3 Cold
  - Priority badge: 🔥 P1 / ⚡ P2 / ❄️ P3
  - Confidence meter (0-100%)

- **Routing Decision**:
  - Destination: Account Executive / SDR / Nurture Campaign
  - Owner type and priority
  - Routing reason

- **AI Reasoning Box** (CRITICAL - most important element):
  ```
  ┌─ 🤖 AI Analysis & Reasoning ─────────────────────────┐
  │                                                       │
  │  [VERDICT: P1] This lead scores 0.85 calculated as: │
  │                                                       │
  │  1. TITLE: Chief Technology Officer = 0.30 points    │
  │  2. COMPANY SIZE: 5000 employees, $50M revenue =     │
  │     0.25 points                                       │
  │  3. INDUSTRY: Technology = 0.15 points                │
  │  4. BUYING SIGNALS: Rating=Hot (0.10), Source=      │
  │     Partner Referral (0.08), keywords=budget,        │
  │     timeline, project (0.06) = 0.24 total            │
  │  5. SAP BONUS: N/A = 0.00 points                     │
  │                                                       │
  │  TOTAL: 0.94 points → Final Score: 0.85             │
  │                                                       │
  │  CONCLUSION: Immediate Account Executive engagement  │
  │  recommended                                          │
  │                                                       │
  └───────────────────────────────────────────────────────┘
  ```
  - Must be prominent, readable, with monospace font
  - Show step-by-step calculation
  - Highlight the final score and conclusion

- **Key Factors** (as chips/tags):
  - "C-level title (CTO)"
  - "Enterprise company (5000 employees)"
  - "Hot rating"
  - "Partner Referral source"
  - "Budget approved in description"

- **SAP Business Context** (if available):
  - Business Partner ID
  - Total Orders
  - Lifetime Revenue
  - Credit Rating
  - Last Order Date
  - "✅ Existing Customer" badge

- **Recommended Action**:
  - Next steps for sales team
  - Timeline suggestions

- **Email Status** (if score >= 0.60):
  - ✅ "Email sent to sales agent" badge
  - Recipient email address
  - Message ID (if available)

#### 3. **Complaint Classification Page**

**Form Fields**:
- Case Number (text input, optional)
- Subject (text input)
- Description (textarea, large - this is critical for classification)
- Priority (dropdown): Low / Medium / High / Critical
- Origin (dropdown): Web / Email / Phone / Other

**Quick Templates** (for demo):
- "Product: Switch Issue" - Pre-fills with switch complaint
- "Product: Cable Problem" - Pre-fills with cable complaint
- "IT: Portal Access" - Pre-fills with IT support request
- "IT: Password Reset" - Pre-fills with password issue
- "General: Product Inquiry" - Pre-fills with general question

**Result Display** (after API call):
- **Classification Result**:
  - Type badge:
    - 📦 "PRODUCT COMPLAINT" (red) → Goes to Product Expert
    - 💻 "IT SUPPORT REQUEST" (blue) → Goes to Services Agent
    - 📋 "GENERAL INQUIRY" (gray) → Goes to Product Expert (default)
  
  - Product Category (if product complaint):
    - SWITCHES / CABLES / CONNECTORS / SOFTWARE / INFRASTRUCTURE / GENERAL
    - Product Name (if identified)
  
  - Confidence meter (0-100%)

- **Sentiment & Urgency**:
  - Sentiment: 😠 Angry / 😤 Frustrated / 😐 Neutral / 😊 Positive
  - Urgency badge: CRITICAL / HIGH / MEDIUM / LOW (color-coded)

- **AI Reasoning Box** (CRITICAL):
  ```
  ┌─ 🤖 AI Agent Analysis ───────────────────────────────┐
  │                                                       │
  │  This is clearly a product complaint about a Belden  │
  │  switch. The description mentions a specific         │
  │  Hirschmann switch model (RS20-0800T1T1SDAEHC) that  │
  │  is malfunctioning. The issue is affecting            │
  │  production, indicating urgency. This should be        │
  │  routed to the Product Expert team for technical      │
  │  support.                                             │
  │                                                       │
  └───────────────────────────────────────────────────────┘
  ```

- **Routing Decision**:
  - Action: "Email to Product Expert" / "Email to Services Agent"
  - Recipient email
  - IT Support Portal link (if IT support)

- **Suggested Response** (editable textarea):
  - Pre-filled with AI-generated response
  - Can be edited before sending

- **Email Status**:
  - ✅ "Email sent to [recipient]" badge
  - Recipient email address
  - Message ID (if available)

#### 4. **History/Activity Log Page**
- List of all queries (leads and tickets)
- Filters:
  - Type: All / Leads / Tickets
  - Date range
  - Score range (for leads)
  - Classification type (for tickets)
- Expandable cards showing:
  - Full request data
  - Full response data
  - Execution time
  - Timestamp
- Export to CSV/JSON option

---

## 🎨 VISUAL DESIGN

### Color Palette (Belden Brand Inspired)
- **Primary**: #1E3A5F (Dark blue - Belden corporate)
- **Success/P1 Hot**: #10B981 (Green)
- **Warning/P2 Warm**: #F59E0B (Orange/Amber)
- **Danger/P3 Cold**: #EF4444 (Red)
- **Product Complaint**: #EF4444 (Red)
- **IT Support**: #3B82F6 (Blue)
- **Background**: #F8FAFC (Light gray)
- **Cards**: #FFFFFF (White with subtle shadow)
- **Text Primary**: #1F2937 (Dark gray)
- **Text Secondary**: #6B7280 (Medium gray)

### Typography
- **Headlines**: Inter or SF Pro Display (700 weight)
- **Body**: Inter or system-ui (400-500 weight)
- **Monospace** (for reasoning, JSON): JetBrains Mono or Fira Code
- **Sizes**: 
  - H1: 32px
  - H2: 24px
  - H3: 20px
  - Body: 16px
  - Small: 14px

### Component Styles
- **Cards**: White background, rounded corners (12px), subtle shadow
- **Buttons**: Rounded (8px), padding 12px 24px, smooth transitions
- **Inputs**: Rounded (8px), border 1px solid #E5E7EB, focus: blue border
- **Badges**: Rounded pills (20px), padding 6px 14px
- **Progress Bars**: Rounded (4px), animated fill
- **Animations**: Smooth transitions (200-300ms), fade-in for results

### Layout
- **Desktop**: Max width 1200px, centered
- **Mobile**: Full width, stacked layout
- **Grid**: Use CSS Grid or Flexbox
- **Spacing**: Consistent 16px, 24px, 32px spacing scale

---

## 🛠️ TECHNOLOGIES

**Recommended Stack**:

**Option A: React + TypeScript + Tailwind (Recommended)**
```bash
npx create-react-app belden-ai-frontend --template typescript
npm install tailwindcss @headlessui/react @heroicons/react
npm install axios react-query framer-motion
```

**Option B: Next.js 14+ (Full-stack ready)**
```bash
npx create-next-app@latest belden-ai-frontend --typescript --tailwind
npm install axios @tanstack/react-query framer-motion
```

**Option C: Vue 3 + TypeScript**
```bash
npm create vue@latest belden-ai-frontend
npm install tailwindcss axios @vueuse/core
```

**Option D: Vanilla HTML/CSS/JS** (Simplest)
- Modern ES6+ JavaScript
- CSS with CSS Variables
- Fetch API for requests

---

## 📁 SUGGESTED FILE STRUCTURE

```
belden-ai-frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── ScoreDisplay.tsx
│   │   │   ├── ReasoningBox.tsx
│   │   │   ├── PriorityBadge.tsx
│   │   │   ├── ConfidenceMeter.tsx
│   │   │   ├── SentimentBadge.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── leads/
│   │   │   ├── LeadForm.tsx
│   │   │   ├── LeadResult.tsx
│   │   │   └── SAPContextCard.tsx
│   │   ├── tickets/
│   │   │   ├── TicketForm.tsx
│   │   │   ├── TicketResult.tsx
│   │   │   ├── ClassificationBadge.tsx
│   │   │   └── QuickTemplates.tsx
│   │   └── dashboard/
│   │       ├── MetricsCard.tsx
│   │       ├── ActivityFeed.tsx
│   │       └── SystemStatus.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── LeadQualification.tsx
│   │   ├── ComplaintClassification.tsx
│   │   └── History.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── hooks/
│   │   ├── useLeadQualification.ts
│   │   └── useComplaintClassification.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── validators.ts
│   └── App.tsx
├── public/
│   └── favicon.ico
├── package.json
└── README.md
```

---

## 📝 TEST DATA

### High-Value Lead (Score ~0.85, sends email)
```json
{
  "Company": "TechCorp Industries",
  "FirstName": "Jane",
  "LastName": "Smith",
  "Title": "Chief Technology Officer",
  "Email": "jane.smith@techcorp.com",
  "Industry": "Technology",
  "Rating": "Hot",
  "AnnualRevenue": 50000000,
  "NumberOfEmployees": 5000,
  "LeadSource": "Partner Referral",
  "Description": "We are expanding our manufacturing facilities and need industrial network infrastructure. Budget approved for Q2 2024."
}
```

### Medium-Value Lead (Score ~0.55, no email)
```json
{
  "Company": "MidTech Solutions",
  "FirstName": "Sarah",
  "LastName": "Williams",
  "Title": "Director of IT",
  "Email": "s.williams@midtech.com",
  "Industry": "Technology",
  "Rating": "Warm",
  "AnnualRevenue": 8000000,
  "NumberOfEmployees": 250,
  "LeadSource": "Web",
  "Description": "We are evaluating network solutions for our office expansion."
}
```

### Product Complaint (Switch)
```json
{
  "Subject": "Hirschmann Switch Keeps Restarting",
  "Description": "Our Hirschmann industrial switch has been restarting every 2-3 hours for the past week. This is affecting our production line. The switch is model RS20-0800T1T1SDAEHC. This is urgent.",
  "Priority": "High",
  "Origin": "Web"
}
```

### IT Support (Portal Access)
```json
{
  "Subject": "Cannot Access Customer Portal",
  "Description": "I cannot log into the customer portal. My password doesn't work and the password reset link is not being sent to my email.",
  "Priority": "Medium",
  "Origin": "Web"
}
```

---

## ✅ DELIVERABLES

1. **Complete source code** (functional and tested)
2. **README.md** with:
   - Installation instructions
   - Environment variables setup
   - API endpoint configuration
   - Development commands
3. **Screenshots or GIFs** showing:
   - Dashboard
   - Lead qualification flow
   - Complaint classification flow
   - Results display with AI reasoning
4. **Package.json** with all dependencies
5. **Environment configuration** (.env.example)

---

## 🎯 PRIORITIES

1. **CRITICAL**: Display AI Reasoning prominently - this is the most important element for the demo
2. **HIGH**: Clear score visualization with color coding
3. **HIGH**: Step-by-step calculation display for lead scoring
4. **HIGH**: Classification result with proper routing indication
5. **MEDIUM**: Form validation and error handling
6. **MEDIUM**: Smooth animations and transitions
7. **MEDIUM**: Responsive design (mobile-friendly)
8. **LOW**: Dark mode toggle

---

## 🚀 GETTING STARTED

1. **Set up the project** with your chosen tech stack
2. **Create the API service** layer to handle requests
3. **Build the Lead Qualification page first** (main use case)
4. **Add Complaint Classification page**
5. **Create Dashboard** with metrics
6. **Add History/Activity log**
7. **Polish UI** and add animations

---

## 🔐 AUTHENTICATION HANDLING

For **local development** (http://localhost:8000):
- No authentication needed
- Direct API calls

For **Vertex AI Agent Engine**:
- Need Bearer token from `gcloud auth print-access-token`
- Token expires in ~1 hour
- Options:
  1. Input field to paste token
  2. Backend proxy that handles auth
  3. Service account integration (advanced)

For **demo purposes**, you can:
- Hardcode a token temporarily (with warning)
- Use a token input field
- Create a simple backend proxy

---

## 📚 ADDITIONAL RESOURCES

- **GitHub Repo**: https://github.com/javierherrera1996/langgraph-salesforce-sap-demo
- **API Documentation**: See `docs/API_ENDPOINTS.md`
- **Test Cases**: See `demo/test_cases.json` and `demo/quick_test_cases.json`
- **Architecture**: See `docs/ARCHITECTURE_OVERVIEW.md`
- **Belden Website**: https://www.belden.com/ (for design inspiration)

---

## 🎨 DESIGN INSPIRATION

Visit https://www.belden.com/ for:
- Color scheme
- Typography
- Layout patterns
- Professional, enterprise feel

The interface should feel:
- **Professional** and enterprise-grade
- **Modern** with clean design
- **Trustworthy** (important for AI decisions)
- **Clear** and easy to understand
- **Fast** and responsive

---

## ⚠️ IMPORTANT NOTES

1. **AI Reasoning is CRITICAL** - Make it the most prominent element in results
2. **Score calculation** should be visible step-by-step for transparency
3. **Email status** should be clearly indicated when emails are sent
4. **Classification routing** should be obvious (Product Expert vs Services Agent)
5. **All text in English** - no Spanish
6. **Error handling** - Show clear error messages if API calls fail
7. **Loading states** - Show spinners/loading indicators during API calls
8. **Responsive** - Should work on desktop, tablet, and mobile

---

Start by creating the project structure and the Lead Qualification page, as it's the primary use case. Then add Complaint Classification and finally the Dashboard.

Do you have any questions before starting?
```

---

## 📋 Additional Notes for Frontend Agent

- The API uses **deterministic scoring** - same input should give same score
- Lead scores are calculated using a **point-based formula** (shown in reasoning)
- Complaint classification distinguishes between **Product** (red) and **IT/Services** (blue)
- **All emails are sent automatically** when conditions are met (score >= 0.60 for leads, always for tickets)
- The `reasoning` field contains formatted text with `\n` line breaks - render with `white-space: pre-wrap`
- All timestamps are in UTC format
- The API returns execution time - you can display this for performance metrics

---

## 🔗 Quick Reference

**Local API**: `http://localhost:8000`
- `/run/lead` - Lead qualification
- `/run/ticket` - Complaint classification  
- `/health` - Health check
- `/status/config` - Configuration status

**Test Data**: See `demo/test_cases.json` for comprehensive examples
