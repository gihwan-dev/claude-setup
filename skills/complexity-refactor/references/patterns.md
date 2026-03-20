# Refactoring Patterns

## 1. Early Return

Handle exceptional cases at the start of the function to reduce indentation in the core logic.

### Before (complexity: 5)

```typescript
function processOrder(order: Order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.payment) {
        if (order.payment.verified) {
          // The core logic is buried deep inside...
          return executeOrder(order)
        } else {
          return { error: 'Payment not verified' }
        }
      } else {
        return { error: 'Missing payment information' }
      }
    } else {
      return { error: 'No items in order' }
    }
  } else {
    return { error: 'No order provided' }
  }
}
```

### After (complexity: 5, but far more readable)

```typescript
function processOrder(order: Order) {
  // Handle exceptional cases first
  if (!order) return { error: 'No order provided' }
  if (order.items.length === 0) return { error: 'No items in order' }
  if (!order.payment) return { error: 'Missing payment information' }
  if (!order.payment.verified) return { error: 'Payment not verified' }

  // The core logic stays flat and clear
  return executeOrder(order)
}
```

## 2. Step-by-Step

Split a long function into logical stages and move each stage into its own function.

### Before (complexity: 12)

```typescript
function registerUser(data: FormData) {
  // 50 lines of validation logic
  if (!data.email) throw new Error('Email is required')
  if (!data.email.includes('@')) throw new Error('Invalid email format')
  // ... 10 more validation checks

  // 30 lines of normalization logic
  const normalizedEmail = data.email.toLowerCase().trim()
  const normalizedPhone = data.phone.replace(/[^0-9]/g, '')
  // ... more normalization

  // 40 lines of persistence logic
  const user = { email: normalizedEmail, phone: normalizedPhone }
  await db.users.insert(user)
  await sendEmail(user.email, 'welcome')
  await logActivity('user_created', user.id)
  // ...

  return user
}
```

### After (each function complexity: 3-4)

```typescript
function registerUser(data: FormData) {
  const validated = validateRegistration(data)
  const normalized = normalizeUserData(validated)
  const user = saveNewUser(normalized)
  return user
}

function validateRegistration(data: FormData) {
  if (!data.email) throw new Error('Email is required')
  if (!data.email.includes('@')) throw new Error('Invalid email format')
  if (!data.password) throw new Error('Password is required')
  if (data.password.length < 8) throw new Error('Password must be at least 8 characters')
  return data
}

function normalizeUserData(data: FormData) {
  return {
    email: data.email.toLowerCase().trim(),
    phone: data.phone.replace(/[^0-9]/g, ''),
    name: data.name.trim(),
  }
}

function saveNewUser(userData: UserData) {
  const user = await db.users.insert(userData)
  await sendWelcomeEmail(user.email)
  await logUserCreated(user.id)
  return user
}
```

## 3. Strategy Pattern

Replace a complex `switch` / `if-else` branch chain with an object map.

### Before (complexity: 8)

```typescript
function calculateDiscount(userType: string, amount: number) {
  if (userType === 'vip') {
    return amount * 0.3
  } else if (userType === 'gold') {
    return amount * 0.2
  } else if (userType === 'silver') {
    return amount * 0.1
  } else if (userType === 'bronze') {
    return amount * 0.05
  } else if (userType === 'new') {
    return amount * 0.15
  } else {
    return 0
  }
}
```

### After (complexity: 1)

```typescript
const DISCOUNT_RATES: Record<string, number> = {
  vip: 0.3,
  gold: 0.2,
  silver: 0.1,
  bronze: 0.05,
  new: 0.15,
}

function calculateDiscount(userType: string, amount: number) {
  const rate = DISCOUNT_RATES[userType] ?? 0
  return amount * rate
}
```

## 4. Extract Condition

Extract a complex condition into a meaningfully named variable or helper function.

### Before

```typescript
if (user.age >= 18 && user.hasId && !user.isBanned && user.emailVerified &&
    (user.subscription === 'premium' || user.trialDaysLeft > 0)) {
  // ...
}
```

### After

```typescript
const isAdult = user.age >= 18
const hasValidIdentity = user.hasId && !user.isBanned && user.emailVerified
const hasAccess = user.subscription === 'premium' || user.trialDaysLeft > 0

const canAccessContent = isAdult && hasValidIdentity && hasAccess

if (canAccessContent) {
  // ...
}

// Or as a function:
function canUserAccessContent(user: User): boolean {
  const isAdult = user.age >= 18
  const hasValidIdentity = user.hasId && !user.isBanned && user.emailVerified
  const hasAccess = user.subscription === 'premium' || user.trialDaysLeft > 0

  return isAdult && hasValidIdentity && hasAccess
}
```

## 5. Null Object / Default

Use a default object instead of repeating null checks.

### Before (complexity: 6)

```typescript
function displayUserInfo(user: User | null) {
  if (user) {
    if (user.name) {
      console.log(user.name)
    } else {
      console.log('No name')
    }
    if (user.email) {
      console.log(user.email)
    } else {
      console.log('No email')
    }
  } else {
    console.log('No user')
  }
}
```

### After (complexity: 1)

```typescript
const ANONYMOUS_USER: User = {
  name: 'No name',
  email: 'No email',
}

function displayUserInfo(user: User | null) {
  const displayUser = user ?? ANONYMOUS_USER
  console.log(displayUser.name)
  console.log(displayUser.email)
}
```

## Pattern Selection Guide

| Situation | Recommended pattern |
|------|----------|
| Nested `if-else` | Early Return |
| Function longer than 50 lines | Step-by-Step |
| More than 5 `switch` / `case` branches | Strategy |
| Complex conditional expression | Extract Condition |
| Repeated null checks | Null Object |
