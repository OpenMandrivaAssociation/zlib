%define shortname z
%define major 1
%define libname %mklibname %{shortname}%{major}
%define biarchname lib%{shortname}%{major}
%define develname %mklibname %{shortname} -d
%define libminizip %mklibname minizip %{major}
%define minizip_devel %mklibname minizip -d

%define build_biarch 0
# Enable bi-arch build on ppc64, sparc64 and x86-64
%ifarch sparcv9 sparc64 x86_64 ppc64
%define build_biarch 1
%endif
%ifarch sparcv9
%define _lib	lib64
%endif

%bcond_without uclibc
%bcond_without dietlibc
%bcond_without minizip

Summary:	The zlib compression and decompression library
Name:		zlib
Version:	1.2.8
Release:	4
Group:		System/Libraries
License:	BSD
URL:		http://www.gzip.org/zlib/
Source0:	http://www.zlib.net/%{name}-%{version}.tar.gz
Patch1:		zlib-1.2.6-multibuild.patch
Patch2:		zlib-1.2.7-get-rid-of-duplicate-pkgconfig-lib-search-path.patch
BuildRequires:	setarch
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.33.2-15
%endif
%if %{with dietlibc}
BuildRequires:	dietlibc-devel
%endif
%if %{with minizip}
BuildRequires:	zlib-devel
%endif

%if %{with minizip}
%package -n %{libminizip}
Summary:	Minizip manipulates files from a .zip archive
Group:		System/Libraries

%description -n %{libminizip}
Minizip manipulates files from a .zip archive.

%package -n %{minizip_devel}
Summary:	Development files for the minizip library
Group:		Development/C
Requires:	%{libminizip} = %{version}-%{release}
Requires:	zlib-devel = %{version}-%{release}
Provides:	libminizip-devel = %{version}-%{release}
Provides:	minizip-devel = %{version}-%{release}

%description -n %{minizip_devel}
This package contains the libraries and header files needed for
developing applications which use minizip.
%endif

%description
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.

%package -n %{libname}
Summary:	The zlib compression and decompression library
Group:		System/Libraries
%rename		%{_lib}zlib1
%rename		%{name}
%rename		%{name}1

%description -n	%{libname}
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.

%if %{build_biarch}
%package -n %{biarchname}
Summary:	The zlib compression and decompression library - biarch
Group:		System/Libraries
Conflicts:	zlib1 < 1.2.6-3

%description -n %{biarchname}
This package contains the zlib biarch library.
%endif

%if %{with uclibc}
%package -n uclibc-%{libname}
Summary:	The zlib compression and decompression library linked against uClibc
Group:		System/Libraries
Conflicts:	zlib1 < 1.2.6-4

%description -n	uclibc-%{libname}
This package contains a version of the zlib library that's built against the
uClibc library.
%endif

%package -n %{develname}
Summary:	Header files and libraries for developing apps which will use zlib
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
%if %{build_biarch}
Requires:	%{biarchname} = %{version}-%{release}
%endif
%if %{with uclibc}
Requires:	uclibc-%{libname} = %{version}
%endif
%rename		%{_lib}zlib-devel
%rename		%{name}-devel
%rename		%{name}1-devel

%description -n	%{develname}
The zlib-devel package contains the header files and libraries needed
to develop programs that use the zlib compression and decompression
library.

Install the zlib-devel package if you want to develop applications that
will use the zlib library.

%prep
%setup -q
%patch1 -p1 -b .multibuild~
%patch2 -p1 -b .pc_libpath~

%build
#(peroyvind): be sure to remove -m64/-m32 flags as they're not overridable
RPM_OPT_FLAGS="`echo $RPM_OPT_FLAGS| sed -e 's/-m.. //g'` -O3"
mkdir objs
pushd objs
  CFLAGS="$RPM_OPT_FLAGS" LDFLAGS="%{?ldflags}" CC="%{__cc}" \
%if %{build_biarch}
  CC="%{__cc} -m64" \
%endif
  ../configure --shared --prefix=%{_prefix} --libdir=%{_libdir}
  export LDFLAGS="$LDFLAGS -Wl,-z,relro"
  sed -i 's/CC=gcc/CC=%{__cc}/g' Makefile
  sed -i 's/LDSHARED=gcc/LDSHARED=%{__cc}/g' Makefile
  %make
  make test
  ln -s ../zlib.3 .
popd

%if %{build_biarch}
%ifarch %{sparcx}
RPM_OPT_FLAGS_32="$RPM_OPT_FLAGS"
%else
RPM_OPT_FLAGS_32=`linux32 rpm --eval %%optflags|sed -e 's#i586#pentium4#g'`
%endif
mkdir objs32
pushd objs32
  CFLAGS="$RPM_OPT_FLAGS_32" LDFLAGS="%{?ldflags}" CC="%{__cc} -m32" \
  ../configure --shared --prefix=%{_prefix}
  %make
  make test
  ln -s ../zlib.3 .
popd
%endif

%if %{with dietlibc}
mkdir objsdietlibc
pushd objsdietlibc
  CFLAGS="-Os" CC="diet gcc" \
  ../configure --prefix=%{_prefix}
  %make libz.a
popd
%endif

%if %{with uclibc}
mkdir objsuclibc
pushd objsuclibc
  CFLAGS="%{uclibc_cflags}" LDFLAGS="%{?ldflags}" CC="%{uclibc_cc}" \
  ../configure --shared --prefix=%{_prefix}
  %make
popd
%endif

%if %{with minizip}
pushd contrib/minizip
autoreconf --install
%configure --enable-static=no
%make
popd
%endif

%install
install -d %{buildroot}%{_prefix}
install -d %{buildroot}%{_libdir}

make install -C objs prefix=%{buildroot}%{_prefix} libdir=%{buildroot}%{_libdir}
%if %{build_biarch}
make install-libs -C objs32 prefix=%{buildroot}%{_prefix}
%endif

install -d %{buildroot}/%{_lib}
mv %{buildroot}%{_libdir}/libz.so.%{major}* %{buildroot}/%{_lib}/
ln -srf %{buildroot}/%{_lib}/libz.so.%{major}.* %{buildroot}%{_libdir}/libz.so

%if %{build_biarch}
install -d %{buildroot}/lib
mv %{buildroot}%{_prefix}/lib/libz.so.%{major}* %{buildroot}/lib/
ln -srf %{buildroot}/lib/libz.so.%{major}.* %{buildroot}%{_prefix}/lib/libz.so
%endif

%if %{with dietlibc}
install -m644 objsdietlibc/libz.a -D %{buildroot}%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif

%if %{with uclibc}
#install -m644 objsuclibc/libz.a -D %{buildroot}%{uclibc_root}%{_libdir}/libz.a
make install-libs-only -C objsuclibc prefix=%{buildroot}%{uclibc_root} libdir=%{buildroot}%{uclibc_root}%{_libdir}
%endif

%if %{with minizip}
pushd contrib/minizip
%makeinstall_std
popd
%endif


%files -n %{libname}
%doc README
/%{_lib}/libz.so.%{major}*

%if %{build_biarch}
%files -n %{biarchname}
/lib/libz.so.*
%endif

%if %{with uclibc}
%files -n uclibc-%{libname}
%{uclibc_root}%{_libdir}/libz.so.%{major}*
%endif

%files -n %{develname}
%doc README ChangeLog doc/algorithm.txt
%{_mandir}/man3/zlib.3*
%{_libdir}/*.a
%{_libdir}/*.so
%{_libdir}/pkgconfig/zlib.pc
# these needs to be installed, otherwise it won't be possible to link against
# it if building for 32 bit on 64 bit
%if %{build_biarch}
%{_prefix}/lib/*.a
%{_prefix}/lib/*.so
%{_prefix}/lib/pkgconfig/zlib.pc
%endif
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.so
%endif
%{_includedir}/*.h
%if %{with dietlibc}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.a
%endif
%if %{with minizip}
%exclude %{_libdir}/libminizip.so
%endif

%if %{with minizip}
%files -n %{libminizip}
%{_libdir}/libminizip.so.%{major}*

%files -n %{minizip_devel}
%{_libdir}/pkgconfig/minizip.pc
%{_libdir}/libminizip.so
%{_includedir}/minizip
%endif

%changelog
* Wed Dec 12 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.7-7
- rebuild on ABF

* Sun Oct 28 2012 Tomasz Pawel Gajc <tpg@mandriva.org> 1.2.7-6
+ Revision: 820166
- fix wrong requires

* Sun Oct 28 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.7-5
+ Revision: 820101
- add missing buildrequires on uClibc package

* Fri Sep 21 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.7-4
+ Revision: 817227
- fix duplicate symlinks found under both /lib & /usr/lib

* Wed Aug 15 2012 Lev Givon <lev@mandriva.org> 1.2.7-3
+ Revision: 814857
- Rebuild.

* Fri Jun 29 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.7-2
+ Revision: 807512
- don't remove devel files for 32 bit biarch

* Wed Jun 20 2012 Oden Eriksson <oeriksson@mandriva.com> 1.2.7-1
+ Revision: 806475
- 1.2.7

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - rebuild against new uClibc

* Fri Mar 09 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.6-6
+ Revision: 783703
- rebuild fixed uClibc() dependencies

* Wed Mar 07 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.6-5
+ Revision: 782570
- reenable dietlibc & uClibc build

* Wed Mar 07 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.6-4
+ Revision: 782566
- disable dietlibc build too for now..
- disable uclibc build for now
- split out uClibc library into separate uclibc-%%{_lib}z1 package

* Tue Feb 21 2012 Matthew Dawkins <mattydaw@mandriva.org> 1.2.6-3
+ Revision: 778714
- split biarch lib from main lib (64bit only)
- made proper lib and devel lib names
- remove biarched devel libraries and pkgconfig file

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - use %%sparcx rather than no longer existing %%sunsparc macro
    - use %%rename all throughout (fixes self-obsoletion while at it)

* Mon Jan 30 2012 Paulo Andrade <pcpa@mandriva.com.br> 1.2.6-2
+ Revision: 769917
- Revert to commit 705557 and upgrade to zlib 1.2.6 from that version.

* Mon Jan 30 2012 Bernhard Rosenkraenzer <bero@bero.eu> 1.2.6-1
+ Revision: 769887
- Update to 1.2.6

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - be sure to compile dietlibc version with -fPIC on x86_64
    - add back sparc support
    - drop useless provides
    - use %%rename for uClibz-zlib1 and drop unnecessary one on uClibc-zlib
    - revert layout messing
    - revert reckless vandalism

  + Paulo Andrade <pcpa@mandriva.com.br>
    - Use same approach used for glibc in multilib split.
    - Split multiarch runtime libraries.
    - Use the same spec format of gcc and newer glibc spec with split multilib.
    - Create a proper check spec section.
    - Define helper macros and prepare for multilib split.
    - Drop untested sparc build
    - Rename build_biarch to build_multiarch

  + Alexander Barakin <abarakin@mandriva.org>
    - fix postprog stage error
    - remove buildroot
    - change "source" to "source0"
    - macro in comment
    - imported package zlib

* Thu Jul 28 2011 Andrey Bondrov <abondrov@mandriva.org> 1.2.5-10
+ Revision: 692108
- Rebuild

* Mon Jul 18 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.5-8
+ Revision: 690258
- build 32 bit biarch version for x86 with -march=pentium4

* Tue Jul 12 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.5-7
+ Revision: 689701
- rebuild against latest uClibc

* Tue May 17 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.5-6
+ Revision: 675827
- rebuild against new uClibc & clean out legacy junk while at it

* Thu Apr 21 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.5-5
+ Revision: 656579
- rebuild against new uClibc
- revert incorrectly applied library packaging policy (long overdue..)

* Fri Dec 17 2010 Funda Wang <fwang@mandriva.org> 1.2.5-3mdv2011.0
+ Revision: 622614
- add gentoo patch to fix building of downstream packages
- use own own ldflags

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - remove scriptlets for long dead releases

* Tue Nov 30 2010 Funda Wang <fwang@mandriva.org> 1.2.5-2mdv2011.0
+ Revision: 603298
- obsoletes old package name

* Mon Nov 29 2010 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.5-1mdv2011.0
+ Revision: 603123
- don't lower zlib's default compile optimization level, compile with -O3
- add versioned build dependency on clibc to ensure getting working one..
- add new pkgconfig files to %%files
- fix new path to algorithm.txt
- fix multibuild patch
- new release: 1.2.5
- drop obsolete patches fixed upstream
- ditch feeble attempt at multilib...

  + Emmanuel Andry <eandry@mandriva.org>
    - apply library policy

* Wed Jan 06 2010 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.3-15mdv2010.1
+ Revision: 486696
- build shared version of uclibc linked library as well, obsoleting uClibc-zlib
- use %%{uclibc_cflags} for uclibc gcc flags
- add back dietlibc build
- don't create symlinks to headers for uClibc, it's not really required...
- don't build uclibc linked library with debugging information

* Tue Dec 01 2009 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.2.3-14mdv2010.1
+ Revision: 472167
- don't split out uclibc linked zlib after all, do multiarch build in stead
- install header symlinks for uclibc
- split uclibc linked static library into a separate package
- replace dietlibc build with uclibc as dietlibc seems pretty much abandoned...

* Tue Dec 16 2008 Oden Eriksson <oeriksson@mandriva.com> 1.2.3-13mdv2009.1
+ Revision: 314890
- rediffed one fuzzy patch

* Thu Aug 07 2008 Thierry Vignaud <tv@mandriva.org> 1.2.3-12mdv2009.0
+ Revision: 266170
- rebuild early 2009.0 package (before pixel changes)

* Tue Jun 10 2008 Oden Eriksson <oeriksson@mandriva.com> 1.2.3-11mdv2009.0
+ Revision: 217581
- rebuilt against dietlibc-devel-0.32

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers

* Tue May 20 2008 Oden Eriksson <oeriksson@mandriva.com> 1.2.3-10mdv2009.0
+ Revision: 209452
- rebuilt with gcc43

* Tue Mar 04 2008 Oden Eriksson <oeriksson@mandriva.com> 1.2.3-9mdv2008.1
+ Revision: 178766
- rebuild

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Wed Aug 15 2007 Olivier Blin <blino@mandriva.org> 1.2.3-8mdv2008.0
+ Revision: 63510
- build dietlibc library with -Os (better, and fix weird segfault)

* Mon Aug 13 2007 Olivier Blin <blino@mandriva.org> 1.2.3-7mdv2008.0
+ Revision: 62821
- move diet libz in _prefix/lib/dietlibc/lib-_arch (to follow gb's convention)

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - install static dietlibc library in correct place on sparc
    - package is now sparcv9 in stead of sparc64 on on sparc
    - be sure to set 64 bit environment also at link time as compiler on sparc
      defaults to 32 bit


* Thu Jan 25 2007 Olivier Blin <oblin@mandriva.com> 1.2.3-5mdv2007.0
+ Revision: 113526
- build a diet libz-diet.a archive

* Mon Dec 04 2006 Gwenole Beauchesne <gbeauchesne@mandriva.com> 1.2.3-4mdv2007.1
+ Revision: 90324
- fix bi-arch builds with different -m32/-m64 optflags

  + Oden Eriksson <oeriksson@mandriva.com>
    - bzip2 cleanup

* Thu Oct 12 2006 Oden Eriksson <oeriksson@mandriva.com> 1.2.3-3mdv2007.1
+ Revision: 63458
- bunzip patches
- Import zlib

* Wed Oct 05 2005 Gwenole Beauchesne <gbeauchesne@mandriva.com> 1.2.3-2mdk
- make it a biarch package on ppc64

* Fri Jul 22 2005 Nicolas Lécureuil <neoclust@mandriva.org> 1.2.3-1mdk
- New release 1.2.3
- Drop patch 5 ( Merged Upstream )

* Thu Jul 21 2005 Olivier Blin <oblin@mandriva.com> 1.2.2.2-3mdk
- from Vincent Danen: security fix for CAN-2005-2096

* Thu Jan 20 2005 Gwenole Beauchesne <gbeauchesne@mandrakesoft.com> 1.2.2.2-2mdk
- make sure we are compiling DSO with -fPIC in configure tests

* Thu Jan 13 2005 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 1.2.2.2-1mdk
- 1.2.2.2
- drop packager tag

* Thu Dec 02 2004 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 1.2.2.1-1mdk
- 1.2.2.1

* Sat Aug 28 2004 Frederic Lepied <flepied@mandrakesoft.com> 1.2.1.1-3mdk
- fix from Debian

* Tue Jul 13 2004 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 1.2.1.1-2mdk
- change default compile flags only for 32 bits build when building on sparc64

* Sun May 30 2004 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 1.2.1.1-1mdk
- 1.2.1.1
- spec cosmetics

