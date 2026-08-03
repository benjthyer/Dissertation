\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{caltech_thesis}
              [2016/01/28 v0.1
 Caltech thesis class]

% Load memoir
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions\relax
\LoadClass[oneside,12pt]{memoir}

\RequirePackage{etoolbox}

% Overleaf 28 Jan: Page geometry
\RequirePackage[letterpaper,top=1in,bottom=1in,left=1.5in,right=1.5in,headsep=\dimexpr 0.25in-1em,marginparwidth=1.25in]{geometry}

% Page style
\makeoddhead{headings}{}{}{\thepage}
\makeevenhead{headings}{}{}{\thepage}

\RequirePackage{graphicx}

%% Overleaf 24 Jan: Formatting of ToC and lists
\setcounter{tocdepth}{1}
\let\listoffigurestables\listoffigures
\appto{\tableofcontents}{\clearpage}
\appto{\listoffigurestables}{\clearpage}
\appto{\listoffigures}{\clearpage}
\appto{\listoftables}{\clearpage}
\renewcommand{\contentsname}{Table of Contents}
\renewcommand{\listfigurename}{List of Illustrations}
\renewcommand{\listtablename}{List of Tables}

% \renewcommand{\listfigurename}{List of Illustrations and/or Tables}

\addtocontents{toc}{\protect\vskip 35pt}
\addtocontents{toc}{\protect\SingleSpacing}
\addtocontents{lof}{\protect\vskip 35pt}
%% In case single spacing is desired later
% \addtocontents{lof}{\protect\SingleSpacing}
% \addtocontents{lot}{\protect\SingleSpacing}
\addtocontents{lof}{{\protect\itshape Number}\protect\hfill{\protect\itshape Page}\protect\par}
\addtocontents{lot}{{\protect\itshape Number}\protect\hfill{\protect\itshape Page}\protect\par}

\setlength{\cftbeforechapterskip}{0pt}

%% For formatting chapter numbers as Roman but
%% not touch appendix alphabets
\RequirePackage{xstring}
\newcommand*{\IsInteger}[3]{%
    \IfStrEq{#1}{ }{#3}{%
        \IfInteger{#1}{#2}{#3}%
    }%
}%
\newcommand{\formatchapternumber}[1]{%
  \IsInteger{#1}{\uppercase\expandafter{\romannumeral #1\relax}}{#1}%
}
\renewcommand{\chapternumberline}[1]{\chaptername\space\formatchapternumber{#1}:\space}
\patchcmd{\cftchapterleader}{\bfseries}{\normalfont}{}{}
\renewcommand{\cftchapterfont}{\normalfont}
\renewcommand{\cftchapterpagefont}{\normalfont}
\renewcommand{\cftchapterdotsep}{\cftdotsep}
\setlength{\cftsectionnumwidth}{2em}

% Merged list of figures and tables -- not needed
% \def\table{\def\figurename{Table}\figure}
% \let\endtable\endfigure 

\setlength{\cftbeforefigureskip}{0pt}
\renewcommand{\cftfiguredotsep}{\cftdotsep}
\settowidth\cftfigurenumwidth{\itshape Number}
\renewcommand\cftfigurepresnum{\hfill}
\renewcommand\cftfigureaftersnum{\hskip1em}

\setlength{\cftbeforetableskip}{0pt}
\renewcommand{\cfttabledotsep}{\cftdotsep}
\settowidth\cfttablenumwidth{\itshape Number}
\renewcommand\cfttablepresnum{\hfill}
\renewcommand\cfttableaftersnum{\hskip1em}

\apptocmd{\appendix}{%
  \addtocontents{toc}{%
    \protect\renewcommand{\protect\chaptername}{Appendix}
  }%
}{}{}

% Overleaf, 22 January 2016: \subsection and onwards shouldn't be numbered
\setcounter{secnumdepth}{3}
\RequirePackage{letterspace} % not so heavy...

% Chapter headings
\renewcommand{\insertchapterspace}{}
\setlength{\midchapskip}{\onelineskip}
\setlength{\afterchapskip}{1.5\onelineskip}
\renewcommand{\chapternamenum}{\space\space}
\renewcommand{\chapterheadstart}{\clearforchapter}
\renewcommand{\chapnamefont}{\SingleSpacing\centering\normalfont\normalsize\itshape\textls[250]}
\renewcommand{\chapnumfont}{\normalfont\normalsize\itshape}
\renewcommand{\chaptitlefont}{\SingleSpacing\centering\normalfont\large}
\renewcommand{\printchaptertitle}[1]{\chaptitlefont\MakeUppercase{#1}}

% Add a command to create an extra chapter with TOC entry.
\newcommand{\extrachapter}[2][\@empty]{%
  \chapter*{#2}%
  \addcontentsline{toc}{chapter}{\ifx#1\@empty{#2}\else{#1}\fi}}
  
% Section headings
\setsecheadstyle{\normalfont\bfseries}
\setbeforesecskip{\onelineskip}
\setaftersecskip{1pt}
\setsubsecheadstyle{\normalfont\bfseries}
\setbeforesubsecskip{\onelineskip}
\setaftersubsecskip{1pt}
  
\aliaspagestyle{chapter}{headings}

%
% Define spacing for use on titlepage
%
\def\titleskip{\vskip 4\bigskipamount}      %% Whitespace after title
\def\authorskip{\vskip 2\bigskipamount}     %% Whitespace after author

%
% Additional titlepage definitions
%
\newcommand{\degreeaward}{\gdef\@degreeaward}
\degreeaward{Doctor of Philosophy}                  % Default is Ph.D.

\newcommand{\university}{\gdef\@university}
\university{California Institute of Technology}     % Default is Caltech

\newcommand{\unilogo}{\gdef\@unilogo}
\unilogo{caltech.png}                                  % Caltech logo

\newcommand{\address}{\gdef\@address}
\address{Pasadena, California}                      % Default is Caltech

\newcommand{\copyyear}{\gdef\@copyyear}
\newcommand{\defenddate}{\gdef\@defenddate}
% Overleaf: Updated 21 January 2016; don't put in a default year value
\copyyear{!!!!}
\defenddate{!!!!}

%
% Overleaf: added 21 January 2016
\newcommand{\orcid}[1]{\gdef\@orcid{#1}}
\orcid{xxxxx}
\newcommand{\rightsstatement}[1]{\gdef\@rightsstatement{#1}}
\rightsstatement{All rights reserved}
% The copyright page is new, must conform to CIT requirements
%
\newcommand{\makecopyright}{%
 {\parindent=0pt
 \null              % Forces rest to bottom of page
 \vfill
 \begin{center}
   \SingleSpacing
   \copyright~\@copyyear\par
   \@author\\ORCID: \@orcid\par
   \@rightsstatement\par
 \end{center}}
 \newpage
}               %% End of \makecopyright

\renewcommand{\maketitle}[1][]{%
 \begin{titlingpage}
   \OnehalfSpacing
   \let\footnotesize\small \let\footnoterule\relax \setcounter{page}{1}
   \vskip-\headsep
   \begin{center}
     {\SingleSpacing\Large\@title\par}
     \titleskip
     Thesis by\\
     {\large \@author}\par
     \authorskip
     In Partial Fulfillment of the Requirements for the\\
     degree of\\
     \@degreeaward\par
     \ifstrequal{#1}{logo}{
       \vspace{\stretch{2}}
       \includegraphics[width=2in]{\@unilogo} \\
       \vspace{\stretch{1}}
     }{\vfill}
      \MakeUppercase{\@university}\\
     \@address\par
     \authorskip
     \@copyyear\\
     {\normalsize Defended \@defenddate\par}
   \end{center}
   \vspace*{.5in}
 \end{titlingpage}
 \pagenumbering{roman}
 \setcounter{page}{2}
 \makecopyright
}               %% End of \maketitle


% The abstract and acknowledgments are treated as unnumbered chapters
% with Table of Contents entries.
\renewenvironment{abstract}
  {\extrachapter{Abstract}}
  {\clearpage}
\newenvironment{acknowledgments}
  {\extrachapter{Acknowledgments}}
  {\clearpage}
% although `acknowledgments' is preferred
\newenvironment{acknowledgements}
  {\extrachapter{Acknowledgements}}
  {\clearpage}

% Overleaf: 22 January 2016 -- non-zero paragraph skip
\nonzeroparskip
\setlength{\parindent}{0pt}
\OnehalfSpacing

\nobibintoc

\AtBeginDocument{%
  \@ifpackageloaded{biblatex}{}
  {\usepackage[backend=biber,natbib,style=authoryear]{biblatex}}
  \DeclareFieldFormat{addendum}{}
  \AtBeginBibliography{\SingleSpacing}
  \setlength{\bibitemsep}{\parskip}
  \defbibheading{publishedcontent}{\extrachapter{Published Content and Contributions}}
  \defbibnote{pcinstructions}{[Include a bibliography of published articles or other material that are included as part of the thesis.  Describe your role with the each article and its contents.  Citations must include DOIs or publisher URLs if available electronically.
 
If you are incorporating any third-party material in the thesis, including works that you have authored/co-authored but for which you have transferred copyright, you must indicate that permission has been secured to use the material. For example: ``Fig.~2 reprinted with permission from the copyright holder, {holder name}''

Add the option \texttt{iknowwhattodo} to this environment to dismiss this message.]}
  
  \newenvironment{publishedcontent}[1][]{
    \newtoggle{printinstr}
    \ifstrequal{#1}{iknowwhattodo}
         {\togglefalse{printinstr}}
         {\toggletrue{printinstr}}
    \DeclareFieldFormat{addendum}{\\##1}
    \begin{refsection}
  }{
     \iftoggle{printinstr}{
       \printbibliography[heading=publishedcontent,prenote=pcinstructions]
     }{
       \printbibliography[heading=publishedcontent]
     }
     \end{refsection}
     \citereset
  }
  
  \newcommand{\publishedas}[1]{
    \begin{refsection}
    \nocite{#1}
    \printbibliography[heading=none]
    \end{refsection}
    \citereset
  }
}

% Overleaf: 25 January 2016 -- for nomenclature
\RequirePackage[intoc]{nomencl}
\makenomenclature
\renewcommand{\nompreamble}{\SingleSpacing\itemindent 0pt}
\renewcommand{\nomlabel}[1]{\bfseries #1.}
\renewcommand{\nomentryend}{.}

% Overleaf: 25 January 2016 -- for index
\RequirePackage{imakeidx}
\makeindex[columns=1,options=-s simple_letters]

% Overleaf: 25 January 2016 -- for endnotes
\RequirePackage{endnotes}
\renewcommand{\notesname}{}
\pretocmd{\theendnotes}{\clearpage}{}{}

% Overleaf: 28 January 2016 -- no more pagenumbers in the TOC
\newcommand{\pocketmaterial}{\addtocontents{toc}{\cftpagenumbersoff{chapter}}}

\endinput