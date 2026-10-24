---
title: "How to improve your technical writing skills."
date: "2026-10-24"
description: "Why it's important and how it can help improve your code and research practice."
categories: [Tips]
---

When most scientists think about writing, they think about writing papers. But the ability to write clear, useful technical text matters far beyond the manuscript: in the comments in your code, the instructions you leave for a colleague and the methods you will have to remember in six months' time. It is incredibly useful for anyone in a scientific or technical career.

We all know that we should be concise and get to the point, yet very few of us are taught how to do this explicitly. We pick it up by trial and error, or by copying whatever the people around us do.

For me, the moment this mattered was when I started writing code that I realised other people would go on to read and use and when I found myself reading my old scripts and trying to figure out the code actually did and why I made certain choices. I was made aware that the code alone was not enough, and that it needed adequate documentation to go with it.

Documentation comes in layers, from explaining the lines of code up to a whole website explaining the outline of a project, with each layer answering a different question for a different reader. This post covers three of them and ends with some resources for improving your technical writing in general.

## Docstrings

A **docstring** is a short piece of text, written inside your code, that describes what a function, class or module does. Because it lives next to the code it describes, it is far more likely to stay up to date than a separate document, and tools can read it too. In Python it is the string directly under the `def` line and it shows up when you call `help(my_function)`. In MATLAB the equivalent is the block of comments at the top of a function, which is printed by `help my_function`.

A good docstring usually answers four questions:

- **What does it do?** A one-line summary, written as a command ("Compute the mean firing rate"), followed by more detail if the function needs it.
- **What goes in?** Each argument, its type and its units. A colon is usually used to separate the argument's name from its type.
- **What comes out?** The return value, its type and its shape.
- **What can go wrong?** Any errors raised, assumptions made or edge cases to watch out for.

For example:

```python
def firing_rate(spike_times, window):
    """Compute the mean firing rate of a neuron.

    Parameters
    ----------
    spike_times : array_like
        Times of each spike, in seconds.
    window : float
        Length of the recording window, in seconds. Must be greater than zero.

    Returns
    -------
    float
        Mean firing rate, in spikes per second (Hz).
    """
    return len(spike_times) / window
```

The layout above follows the NumPy convention. Google's style is a popular alternative. The main point is to pick one and use it consistently.

An example docstring in Google's style:

```python 
def func(arg1, arg2):
    """Summary line.

    Extended description of function.

    Args:
        arg1 (int): Description of arg1
        arg2 (str): Description of arg2

    Returns:
        bool: Description of return value

    """
    return True
```

An example docstring in NumPy's style:

```python 
def func(arg1, arg2):
    """Summary line.

    Extended description of function.

    Parameters
    ----------
    arg1 : int
        Description of arg1
    arg2 : str
        Description of arg2

    Returns
    -------
    bool
        Description of return value

    """
    return True
```

The main difference between the two styles is that Google uses indentation to separate sections, whereas NumPy uses underlines. NumPy style tends to require more vertical space, whereas Google style tends to use more horizontal space. Google style tends to be easier to read for short and simple docstrings, whereas NumPy style tends be easier to read for long and in-depth docstrings.


**Resources on writing good docstrings**

- [PEP 257: Docstring conventions](https://peps.python.org/pep-0257/): the official Python guidance on what a docstring is and how to lay it out.
- [numpydoc style guide](https://numpydoc.readthedocs.io/en/latest/format.html): the NumPy docstring format, widely used across scientific Python.
- [Google Python Style Guide: comments and docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings): the Google alternative, with clear examples.
- [MATLAB: add help for your program](https://www.mathworks.com/help/matlab/matlab_prog/add-help-for-your-program.html): how to write help text for MATLAB functions.

## README files

A **README** is a plain-text file, normally called `README.md`, that sits at the top level of a project. It is the first thing someone sees when they open your repository, and on GitHub it is displayed automatically on the project's front page. Think of it as the front door of the project: it should tell a stranger what this is, whether it is useful to them and how to get started.

A good README for a research code project usually covers:

- **What it is.** The name and a short description of what the project does and why it exists.
- **How to install it.** The dependencies and software versions it needs, and the steps to set it up.
- **How to use it.** A minimal working example, or link to one within the repository, plus the expected output.
- **What the data looks like.** Where it comes from, the format it is in and where to download it, if the project uses data.
- **How to get help or contribute.** Who to contact, how to report a problem and how to cite the work.
- **The licence.** What other people are allowed to do with your code.

You don't need to say everything in the README. Keep it short and link out to fuller documentation for the details. If you find the README getting very long, that is a sign that it is time for a documentation site (see below).

**Resources on writing good READMEs**

- [Make a README](https://www.makeareadme.com/): a short, practical guide with a template you can start from.
- [About READMEs (GitHub Docs)](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes): what GitHub does with your README and what to include.
- [The Turing Way: Code documentation](https://book.the-turing-way.org/reproducible-research/code-documentation): advice written for researchers, covering READMEs and the other layers of documentation.

## Documentation sites

Docstrings explain individual functions and a README introduces the whole project. Once a project has several workflows, a few rounds of analysis or more than one person using it, you need somewhere to put the longer explanations: tutorials, the reasoning behind your choices and step-by-step guides. 

A **documentation site** is a website built from plain-text files that holds all of this in one searchable, linkable place. These are free to host on GitHub Pages and can be generated automatically from your docstrings.

I wrote a [separate post](02_quarto.md) on building one with Quarto, including a comparison of the alternatives.

## Recommended resources:

[Google Technical Writing Courses](https://developers.google.com/tech-writing) 
Free online course covering the basics of technical writing. It doesn't offer a certificate but I think just reviewing the content is useful and having it as a reference to come back to. 

[The Turing Way Handbook](https://book.the-turing-way.org/)
***Fantastic*** resource that I found while preparing a presentation on "Documentation, Dashboards and Data Management" for my mentoring group at work. 
Great tips on how to conduct reproducible and ethical research, project design, collaboration and communication. A must read, especially recommended for someone starting out in their research career. It's the resource I wish I had when I started the PhD. 

## Final thoughts

Good documentation is not about writing more, it is about writing for the next person who will open your work, who is very often you. You don't have to do everything at once. Start by adding a docstring to the next function you write, then put a README in the next project you share. Those two habits alone make your work easier to understand, reuse and trust.

I'd love to hear what has helped you, so if there is a resource I've missed, please send it my way.