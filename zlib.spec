%define shortname z
%define major 1
%define libname %mklibname %{shortname} %{major}
%define biarchname lib%{shortname}%{major}
%define devname %mklibname %{shortname} -d
%define libminizip %mklibname minizip %{major}
%define devminizip %mklibname minizip -d
%define _disable_lto 1

%define build_biarch 0
# Enable bi-arch build on ppc64, sparc64 and x86-64
# disabled since 5 July 2016
# biarch seems to be a stuff from mandrake time
# don't know any reason to keep it alive
%ifarch sparcv9 sparc64 ppc64
%define build_biarch 1
%endif
%ifarch sparcv9
%define _lib lib64
%endif
%bcond_without minizip
# (tpg) enable PGO build
%ifnarch riscv64
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	The zlib compression and decompression library
Name:		zlib
Version:	1.2.11
Release:	9
Group:		System/Libraries
License:	BSD
Url:		http://www.gzip.org/zlib/
Source0:	http://www.zlib.net/%{name}-%{version}.tar.xz
Source1:	zlib.rpmlintrc
%if %{build_biarch}
Patch1:		zlib-1.2.6-multibuild.patch
%endif
Patch2:		zlib-1.2.7-get-rid-of-duplicate-pkgconfig-lib-search-path.patch
# https://github.com/madler/zlib/pull/210
Patch6:		zlib-1.2.5-minizip-fixuncrypt.patch
# resolves: RH#844791
Patch7:		zlib-1.2.7-z-block-flush.patch
# resolves: #985344
# http://mail.madler.net/pipermail/zlib-devel_madler.net/2013-August/003081.html
Patch8:		zlib-1.2.8-minizip-include.patch
# (tpg) does this is still needed ?
#Patch9:		zlib-1.2.8-rsync-Z_INSERT_ONLY.patch
# From https://github.com/madler/zlib/commit/f9694097dd69354b03cb8af959094c7f260db0a1.patch
Patch10:	zlib-1.2.11-fix-deflateParams-usage.patch

%ifarch aarch64
# general aarch64 optimizations
Patch20:	0001-Porting-inflate-using-wider-loads-and-stores.patch
Patch21:	0002-Port-Fix-InflateBack-corner-case.patch
Patch22:	0001-Neon-Optimized-hash-chain-rebase.patch
Patch23:	0002-Porting-optimized-longest_match.patch
Patch24:	0003-arm64-specific-build-patch.patch
%endif

BuildRequires:	util-linux
BuildRequires:	kernel-headers

%if %{with minizip}
%package -n %{libminizip}
Summary:	Minizip manipulates files from a .zip archive
Group:		System/Libraries

%description -n %{libminizip}
Minizip manipulates files from a .zip archive.

%package -n %{devminizip}
Summary:	Development files for the minizip library
Group:		Development/C
Requires:	%{libminizip} = %{version}-%{release}
Requires:	%{devname} = %{version}-%{release}
Provides:	minizip-devel = %{version}-%{release}

%description -n %{devminizip}
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
%rename		%{_lib}z1_

%description -n %{libname}
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

%package -n %{devname}
Summary:	Header files and libraries for developing apps which will use zlib
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
%if %{build_biarch}
Requires:	%{biarchname} = %{version}-%{release}
%endif
%rename		%{_lib}zlib-devel
%rename		%{name}-devel
%rename		%{name}1-devel

%description -n %{devname}
This package contains the header files and libraries needed to develop programs
that use the zlib compression and decompression library.

%prep
%autosetup -p1

%build
%serverbuild_hardened

#(peroyvind): be sure to remove -m64/-m32 flags as they're not overridable
RPM_OPT_FLAGS="$(echo $RPM_OPT_FLAGS | sed -e 's/-m.. //g') -O3"

%ifarch aarch64
RPM_OPT_FLAGS+="$RPM_OPT_FLAGS -DARM_NEON"
%endif

%if %{with pgo}
CFLAGS_PGO="$RPM_OPT_FLAGS -fprofile-instr-generate"
CXXFLAGS_PGO="$RPM_OPT_FLAGS -fprofile-instr-generate"
FFLAGS_PGO="$CFLAGS_PGO"
FCFLAGS_PGO="$CFLAGS_PGO"
LDFLAGS_PGO="%{ldflags} -fprofile-instr-generate"
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"
CFLAGS="${CFLAGS_PGO}" CXXFLAGS="${CXXFLAGS_PGO}" FFLAGS="${FFLAGS_PGO}" FCFLAGS="${FCFLAGS_PGO}" LDFLAGS="${LDFLAGS_PGO}" CC="%{__cc}" ./configure --static --shared
sed -i 's|CC=gcc|CC=%{__cc}|g' Makefile
sed -i 's|LDSHARED=gcc|LDSHARED=%{__cc}|g' Makefile

make V=1  %{?_smp_mflags}

cat *.c | ./minigzip -6 | ./minigzip -d > /dev/null
cat *.c | ./minigzip -4 | ./minigzip -d > /dev/null
cat *.c | ./minigzip -9 | ./minigzip -d > /dev/null
llvm-profdata merge --output=%{name}.profile *.profile.d
unset LLVM_PROFILE_FILE
unset LD_LIBRARY_PATH
rm -f *.profile.d
make clean
%endif

mkdir objs
cd objs
%if %{with pgo}
    CFLAGS="$RPM_OPT_FLAGS -fprofile-instr-use=$(realpath ../%{name}.profile)" \
    CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath ../%{name}.profile)" \
    LDFLAGS="%{ldflags} -fprofile-use" \
    CC="%{__cc}" \
%else
    CFLAGS="$RPM_OPT_FLAGS" LDFLAGS="%{?ldflags}" \
    CC="%{__cc}" \
%endif
%if %{build_biarch}
    CC="%{__cc} -m64" \
%endif
    ../configure --shared --prefix=%{_prefix} --libdir=%{_libdir}
    export LDFLAGS="$LDFLAGS -Wl,-z,relro -Wl,-z,now"
    sed -i 's|CC=gcc|CC=%{__cc}|g' Makefile
    sed -i 's|LDSHARED=gcc|LDSHARED=%{__cc}|g' Makefile
    %make_build
    make test
    ln -s ../zlib.3 .
cd -

%if %{build_biarch}
%ifarch %{sparcx}
RPM_OPT_FLAGS_32="$RPM_OPT_FLAGS"
%else
RPM_OPT_FLAGS_32="$(linux32 rpm --eval %%{optflags}|sed -e 's#i586#pentium4#g')"
%endif
mkdir objs32
cd objs32
  # FIXME as of 3.5-0.211571.1, clang -m32 is broken
  # (calls linker in 64bit mode).
  # Force gcc for 32bit builds for now.
  CFLAGS="$RPM_OPT_FLAGS_32" LDFLAGS="%{?ldflags}" CC="gcc -m32" \
  ../configure --shared --prefix=%{_prefix}
  %make_build
  make test
  ln -s ../zlib.3 .
cd -
%endif

%if %{with minizip}
cd contrib/minizip
make clean ||:
autoreconf --install
%if %{with pgo}
    CFLAGS="$RPM_OPT_FLAGS -fprofile-instr-use=$(realpath ../../%{name}.profile)" \
    CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath ../../%{name}.profile)" \
    LDFLAGS="%{ldflags} -fprofile-use" \
    CC="%{__cc}" \
%else
    CFLAGS="$RPM_OPT_FLAGS" LDFLAGS="%{?ldflags}" \
    CC="%{__cc}" \
%endif
LD_LIBRARY_PATH="$(realpath ../../objs)" LDFLAGS="${LDFLAGS} -L$(realpath ../../objs)" %configure --enable-static=no
%make_build
cd -
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

%if %{with minizip}
cd contrib/minizip
%make_install
cd -

rm -fr %{buildroot}%{_libdir}/libminizip.la
# https://bugzilla.redhat.com/show_bug.cgi?id=1424609
# https://github.com/madler/zlib/pull/229
rm -fr %{buildroot}%{_includedir}/minizip/crypt.h
%endif

%files -n %{libname}
%doc README
/%{_lib}/libz.so.%{major}*

%if %{build_biarch}
%files -n %{biarchname}
/lib/libz.so.*
%endif

%files -n %{devname}
%doc README doc/algorithm.txt
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
%{_includedir}/*.h
%if %{with minizip}
%exclude %{_libdir}/libminizip.so
%endif

%if %{with minizip}
%files -n %{libminizip}
%{_libdir}/libminizip.so.%{major}*

%files -n %{devminizip}
%{_libdir}/pkgconfig/minizip.pc
%{_libdir}/libminizip.so
%{_includedir}/minizip
%endif
