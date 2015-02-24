# Contributing

CRITs would not be where it is today without the contributions of users and
developers from across the security industry. We love hearing from users and
contributions are the best thing to hear! Contributions come to us in many
different ways:

* [Mailing list posts][ml]
* IRC channel chats at irc://irc.freenode.net:6667/crits
* [Github Issues][issues]
* [Pull Requests][prs]

[ml]: https://groups.google.com/forum/#!forum/crits-users
[issues]: https://github.com/crits/crits/issues
[prs]: https://github.com/crits/crits/pulls

CRITs is broken out into several projects:

* [Core][core]
  * This is the main code base for the CRITs project.
* [CRITs Services][services]
  * Services are ways of extending the features and functionality of CRITs.
* [pycrits][pc]
  * A python library for interacting with the CRITs Core API.
* [mcrits][mc]
  * Maltego transforms for interacting with the CRITs Core API.
* [crits-hubot][ch]
  * A Hubot designed for interacting with the CRITs Core API.
  * 
[core]: https://github.com/crits/crits
[services]: https://github.com/crits/crits_services
[pc]: https://github.com/crits/pycrits
[mc]: https://github.com/crits/mcrits
[ch]: https://github.com/crits/crits-hubot

If you would like to contribute to any of these projects, you can do the
following:

[Fork][fork] the core repo and then [clone][clone] it locally:

[fork]: https://help.github.com/articles/fork-a-repo/
[clone]: https://help.github.com/articles/which-remote-url-should-i-use/

    git clone git@github.com:your-username/crits

## Install Core
Install the core project. (more to come about this)


## Read the Wiki
Review all of the documentation found on the [wiki][wiki]. This is very
important as there are dozens of pages aimed at explaining how the project is
designed, where to find features, how to develop code for the project, etc.

[wiki]: https://github.com/crits/crits/wiki

## Look for existing issues
Search the Issues for the project to find an existing issue related to the bug
or feature you are looking to fix and/or develop. If there is an existing one,
comment on it to engage with the community. If there is not, create one to
solicit feedback from the community on the bug/feature in question. It is
important to do this to ensure that we are all on the same page, and in agreement
with the nature of the Issue as well as the proposed fix. Once everyone is in
agreement, you can begin development. We can’t stress enough how important it is
to engage and engage often. The more people are familiar with your changes the
easier it will be to look over and accept them when they are ready!

## Branch locally and develop!
Make a branch in your cloned fork. We suggest naming the branch by feature name
or “issue_XX” where XX is the issue number the branch is associated with. Make
your changes in your branch and test thoroughly. If this is a large feature you
can push your branch to your fork often. This allows you to request feedback for
how things are progressing instead of dumping a large code change all at once.

When making commits to your branch, make sure you write [well-formed][wf] commit
messages.

[wf]: https://github.com/erlang/otp/wiki/Writing-good-commit-messages

## Submit a PR
Once you are happy with your changes and ready for a PR, you can submit a PR to
the main project. In most cases you’ll be looking to compare against the Master
branch, but there are instances where you’re making changes that you want to go
into a specific branch. Make sure when submitting your PR that you choose the
right destination branch.

Once you’ve submitted a PR it’s on the community to proceed. In most cases we
like to have a few people get some eyes on the code and the feature to make sure
there’s no general issues. They might require you to go back and make some more
changes (simply edit your local branch and push to the branch associated with
the PR; it will get updated automagically!).

## Misc.
All of the projects will require core to be installed. After that repeat the
process for the other projects you are interested in contributing to!
