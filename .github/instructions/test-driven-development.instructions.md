---
applyTo: '**/.py'
---

# Test Driven Development (TDD) Instructions

Add tests for all new features and bug fixes. Follow the TDD process:

1. **Write a failing test**: Before writing any new code, create a test that defines a function or improvements of a
   function, which should fail initially.
2. **Run the test**: Execute the test to confirm it fails. This ensures that the test is valid and that the new
   functionality is not yet implemented.
3. **Write the minimum code**: Write the simplest code necessary to make the test pass. Focus on getting the test to
   pass without worrying about optimization or refactoring.
4. **Run the test again**: Execute the test suite to confirm that the new code passes the test. If it fails, debug and
   fix the code until it passes.
5. **Refactor the code**: Once the test passes, review the code for any improvements or optimizations. Refactor the code
   while ensuring that all tests still pass.
6. **Repeat**: Continue this process for each new feature or bug fix, ensuring that tests are added for all new
   functionality.
