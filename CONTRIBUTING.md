# How to contribute

We're really glad you're reading this, because we need volunteers to help this project realise its full potential.

If you haven't already, come find us in [Discord](http://discord.gg/vqME6WsPd7) in the `#github` channel.
We want you working on things you're excited about.

Here are some important resources:

  * [GE Github README](https://github.com/garyseconomics/.github/blob/main/profile/README.md) tells you a little about what projects are going on.
  * Each repo's Issues page is the day-to-day project management space.

## Testing

Key functionality should have its own tests.
At the moment (2026-08-03), all the key functionality is already covered by tests.
In future an A.I. code assistant could help evaluate this, but for now we rely on our team leads.
They check each code change before merging a Pull Request to see that new functionality is covered by tests, and that the test are really testing what they should. 

Please check your PRs already pass all the existing tests before moving a PR out of Draft status (or posting it directly), as each PR will be reviewed by someone else.
Ideally all new code should pass the tests locally, before being committed. 

## Submitting changes

Please send changes as GitHub Pull Requests, with a clear summary of what you've done (read more about [pull requests](http://help.github.com/pull-requests/)) and a useful series of commits that each has a clear commit message.
Please follow our coding conventions and make sure all of your commits are atomic (one feature per commit).

A clear commit message can be a one line message for small changes, and bigger changes should look like this, with the first line a short title and then detail in a paragraph body below:

    $ git commit -m "A brief summary of the commit
    > 
    > A paragraph describing what changed and its impact."

When you send a pull request with new code, we will love you forever if you include tests for that code.
We can always use more test coverage.

## Coding conventions

Start reading our code and you'll get the hang of it.
We optimize for readability:

  * We indent using 4 spaces (not tabs)
  * We use [Ruff](https://github.com/astral-sh/ruff) to lint and format Python code
  * This is open source software.
    Consider the people who will read your code, and make it look nice for them.
    It's sort of like driving a car:
    Perhaps you love doing donuts when you're alone, but with passengers the goal is to make the ride as smooth as possible.

Thanks!
