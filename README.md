Temporary render test for the profile redesign (will be deleted).

A: relative srcset with ./

<picture>
  <source media="(max-width: 767px)" srcset="./rt/masthead-narrow.svg">
  <img src="./rt/masthead.svg" width="100%" alt="A">
</picture>

B: relative srcset without ./

<picture>
  <source media="(max-width: 767px)" srcset="rt/masthead-narrow.svg">
  <img src="rt/masthead.svg" width="100%" alt="B">
</picture>

C: plain img

<img src="./rt/masthead-narrow.svg" width="360" alt="C">
