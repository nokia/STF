# STF
- A Simple Test Framework.
- STF is an automation test framework implemented with Python;
- STF can be installed via pip install command;

-------

## STF key features:
- Use directory/file to represent a test case/test steps, great benefit writing cases with script(shell, python, Expect);
- Generate Html report and JUnit xml report for test cases;
- Get case info from Testcase Management System(e.g. zephyr) and report the case status back to TMS;
- Reuse code by various modules rather than functions;
- Can wrap other automation frameworks (e.g. Ansible, Robot...) and user's own private automation framework, easily and intuitively;

--------
## STF Arch
![STF Arch](https://github.com/nokia/STF/blob/master/images/STF_arch.PNG)

--------
## STF test view
STF test view usage:

`stf test -c <your_case_dir>`

STF test view provide 3 kinds of cases:  
1. case directory with case step files;
2. case directory without case step files;
3. one single file as a test case;

A STF case must be independent, since other cases may be omitted after apply filter and will not run during test.

--------
### STF test view - case directory with case step files

- In this situation, STF test case use 1-level directory to represent a test case, and use the files in this directory to represent the test steps;
- STF case directory name format : stf__\<tag>__<caseid1~caseid2...>
- Case step file name format: s\<id>\__\<module>\[~\<parameter>]__\<tag>

--------
### STF test view - case directory without case steps
- In this situation, STF test case use a directory to represent a test case, and you can put any files in this directory;
- STF case directory name format : stfs\<id>\__\<module>\_\_\<tag>__\<caseid1~caseid2...>

--------
### STF test view - one single file as a test case
- In this situation, STF test case use a single file to represent a test case;
- STF case file name format : stfs\<id>\__\<module>\_\_\<tag>__<caseid1~caseid2...>

--------
### STF format explanation
- \<id>  is [1-99999], but the number itself has no special meaning;
- \<module> is <script | vlab | playbook | robot | copy | env>;
- \<tag> is characters you name this case to reflect its' content;
- <caseid1~caseid2...> is the zephyr JIRA ID;

--------
### A STF test view example
With the ability above, stf can create OpenStack instances and run cases on them intuitively:

1. stfs1__vlab~ins1__create__tag1
2. stfs2__script~ins1__run__tag2
3. stfs3__vlab~ins1@d__delete__tag3

--------
### STF Standard output  
- is similar with CGI or fastCGI


--------
## STF with C++ coverage
stf can also help to inject gcov parameters:
    
```
stf gcov -b make all

#Now you can run your program which will generate gcda files
```


