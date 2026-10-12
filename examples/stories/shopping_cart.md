# Shopping cart quantity

As a shopper, I want to change the quantity of an item in my cart so that I can buy the amount I need.

## Acceptance criteria
1. Quantity can be set from 1 to 10 per item using +/- buttons or by typing a number.
2. Setting the quantity to 0 removes the item after a confirmation prompt.
3. Non-numeric or decimal input is rejected with the message "Enter a whole number from 1 to 10".
4. The line total and cart subtotal update immediately when quantity changes.
5. If requested quantity exceeds available stock, quantity is capped at stock level and the user sees "Only N left in stock".
