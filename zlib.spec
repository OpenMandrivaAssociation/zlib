%define shortname z
%define major 1
%define libname %mklibname %{shortname} %{major}
%define biarchname lib%{shortname}%{major}
%define devname %mklibname %{shortname} -d
%define libminizip %mklibname minizip %{major}
%define devminizip %mklibname minizip -d

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
Release:	19
Group:		System/Libraries
License:	BSD
Url:		http://www.gzip.org/zlib/
Source0:	http://www.zlib.net/%{name}-%{version}.tar.gz
Source1:	zlib.rpmlintrc
Patch1:		zlib-1.2.6-multibuild.patch
Patch2:		zlib-1.2.7-get-rid-of-duplicate-pkgconfig-lib-search-path.patch
Patch3:		zlib-1.2.7-improve-longest_match-performance.patch
Patch4:		zlib-format.patch
# This speeds up "minigzip -d linux-3.14.tar.gz" by around 10%
Patch5:		zlib-1.2.8-memcpy.patch
Patch6:		zlib-1.2.5-minizip-fixuncrypt.patch
# resolves: RH#844791
Patch7:		zlib-1.2.7-z-block-flush.patch
# resolves: #985344
# http://mail.madler.net/pipermail/zlib-devel_madler.net/2013-August/003081.html
Patch8:		zlib-1.2.8-minizip-include.patch
Patch9:		zlib-1.2.8-rsync-Z_INSERT_ONLY.patch
BuildRequires:	setarch
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.33.2-15
%endif
%if %{with dietlibc}
BuildRequires:	dietlibc-devel
%endif
%if %{with minizip}
BuildRequires:	pkgconfig(zlib)
%endif

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

%package -n uclibc-%{devname}
Summary:	Header files and libraries for developing apps which will use zlib
Group:		Development/C
Provides:	uclibc-%{name}-devel = %{EVRD}
Requires:	uclibc-%{libname} = %{EVRD}
Requires:	%{devname} = %{EVRD}
Conflicts:	%{devname} < 1.2.8-19

%description -n	uclibc-%{devname}
This package contains the header files and libraries needed to develop programs
that use the zlib compression and decompression library.
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

%description -n	%{devname}
This package contains the header files and libraries needed to develop programs
that use the zlib compression and decompression library.

%prep
%setup -q
%apply_patches

%build
#(peroyvind):	be sure to remove -m64/-m32 flags as they're not overridable
RPM_OPT_FLAGS="`echo $RPM_OPT_FLAGS | sed -e 's/-m.. //g'` -O3"
mkdir objs
pushd objs
  CFLAGS="$RPM_OPT_FLAGS -Ofast" LDFLAGS="%{?ldflags}" CC="%{__cc}" \
%if %{build_biarch}
  CC="%{__cc} -m64" \
%endif
  ../configure --shared --prefix=%{_prefix} --libdir=%{_libdir}
  export LDFLAGS="$LDFLAGS -Wl,-z,relro"
  sed -i 's|CC=gcc|CC=%{__cc}|g' Makefile
  sed -i 's|LDSHARED=gcc|LDSHARED=%{__cc}|g' Makefile
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
  # FIXME as of 3.5-0.211571.1, clang -m32 is broken
  # (calls linker in 64bit mode).
  # Force gcc for 32bit builds for now.
  CFLAGS="$RPM_OPT_FLAGS_32" LDFLAGS="%{?ldflags}" CC="gcc -m32" \
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

%files -n uclibc-%{devname}
%{uclibc_root}%{_libdir}/libz.so
%{uclibc_root}%{_libdir}/libz.a
%endif

%files -n %{devname}
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
%{_includedir}/*.h
%if %{with dietlibc}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif
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
