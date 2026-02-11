# Page snapshot

```yaml
- generic [ref=e4]:
  - heading "Welcome Back" [level=1] [ref=e5]
  - paragraph [ref=e6]: Sign in to your account
  - generic [ref=e7]:
    - generic [ref=e8]:
      - generic [ref=e9]: Email
      - textbox [ref=e10]: player_1770843045263@e2e.test
    - generic [ref=e11]:
      - generic [ref=e12]: Password
      - textbox [active] [ref=e13]: Player123!
    - generic [ref=e14]:
      - checkbox "Beni hatırla" [checked] [ref=e15]
      - text: Beni hatırla
    - button "Log In" [ref=e16] [cursor=pointer]
  - paragraph [ref=e17]:
    - text: Don't have an account?
    - link "Sign Up" [ref=e18] [cursor=pointer]:
      - /url: /register
```