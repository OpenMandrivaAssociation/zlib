%define		libz_major		1
%define		libz			%{name}%{libz_major}
%define		libz_devel		%{libz}-devel
%define		multilibz		libz%{libz_major}

%define		build_multiarch		0
%ifarch x86_64
    %define	build_multiarch		1
%endif

%bcond_without uclibc
%bcond_without dietlibc

#-----------------------------------------------------------------------
Summary:	The zlib compression and decompression library
Name:		zlib
Version:	1.2.5
Release:	10
Group:		System/Libraries
License:	BSD
URL:		http://www.gzip.org/zlib/
Source0:	http://prdownloads.sourceforge.net/libpng/%{name}-%{version}.tar.gz
Patch1:		zlib-1.2.5-multibuild.patch
Patch2:		zlib-1.2.5-lfs-decls.patch
BuildRequires:	setarch
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.32-2
%endif
%if %{with dietlibc}
BuildRequires:	dietlibc-devel
%endif

%description
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.

#-----------------------------------------------------------------------
%package	-n %{libz}
Summary:	The zlib compression and decompression library
Group:		System/Libraries
Obsoletes:	libz, libz1, %{name}
#(proyvind):	library policy applied by error here previously, this is a biarch
#	     	package that ships *both* lib & lib64
%define	liberr	%{mklibname %{name}%{libz_major}}
%rename	%{liberr}
Provides:	libz = %{version}-%{release} libz1 = %{version}-%{release} %{name} = %{version}-%{release}
%if %{with uclibc}
Provides:	uClibc-zlib = %{version}-%{release} uClibc-zlib1 = %{version}-%{release}
Obsoletes:	uClibc-zlib <= %{version}-%{release} uClibc-zlib1 <= %{version}-%{release}
%endif 

%description	-n %{libz}
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.

%files		-n %{libz}
%doc README
/%{_lib}/libz.so.%{libz_major}*
%{_libdir}/libz.so.%{libz_major}*
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.so.%{libz_major}*
%endif
%if %{build_multiarch}
/lib/libz.so.*
%{_prefix}/lib/libz.so.%{libz_major}*
%endif

#-----------------------------------------------------------------------
%package	-n %{libz_devel}
Summary:	Header files and libraries for developing apps which will use zlib
Group:		Development/C
Requires:	%{libz} = %{version}-%{release}
Obsoletes:	libz1-devel libz-devel zlib-devel
%define	deverr	%{mklibname -d %{name}}
%rename	%{deverr}
Provides:	libz-devel = %{version}-%{release} libz1-devel = %{version}-%{release} %{name}-devel = %{version}-%{release}
%if %{with uclibc}
Provides:	uClibc-zlib-devel = %{version}-%{release} uClibc-zlib1-devel = %{version}-%{release}
Obsoletes:	uClibc-zlib-devel <= %{version}-%{release} uClibc-zlib1-devel <= %{version}-%{release}
%endif 

%description	-n %{libz_devel}
The zlib-devel package contains the header files and libraries needed
to develop programs that use the zlib compression and decompression
library.

Install the zlib-devel package if you want to develop applications that
will use the zlib library.

%files		-n %{libz_devel}
%doc README ChangeLog doc/algorithm.txt
%{_mandir}/man3/zlib.3*
%{_libdir}/*.a
%{_libdir}/*.so
%{_libdir}/pkgconfig/zlib.pc
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.so
%endif
%if %{build_multiarch}
%{_prefix}/lib/*.a
%{_prefix}/lib/*.so
%{_prefix}/lib/pkgconfig/zlib.pc
%endif
%{_includedir}/*
%if %{with dietlibc}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.a
%endif

########################################################################
%prep
%setup -q
%patch1 -p1 -b .multibuild~
%patch2 -p1 -b .lfs

#-----------------------------------------------------------------------
%build
#(peroyvind): be sure to remove -m64/-m32 flags as they're not overridable
RPM_OPT_FLAGS="`echo $RPM_OPT_FLAGS| sed -e 's/-m.. //g'` -O3"
mkdir objs
pushd objs
  CFLAGS="$RPM_OPT_FLAGS" LDFLAGS="%{?ldflags}" \
%if %{build_multiarch}
  CC="%{__cc} -m64" \
%endif
  ../configure --shared --prefix=%{_prefix} --libdir=%{_libdir}
  %make
  ln -s ../zlib.3 .
popd

%if %{build_multiarch}
RPM_OPT_FLAGS_32=`linux32 rpm --eval %%optflags|sed -e 's#i586#pentium4#g'`
mkdir objs32
pushd objs32
  CFLAGS="$RPM_OPT_FLAGS_32" LDFLAGS="%{?ldflags}" CC="%{__cc} -m32" \
  ../configure --shared --prefix=%{_prefix}
  %make
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

#-----------------------------------------------------------------------
%check
pushd objs
     make test
popd
%if %{build_multiarch}
pushd objs32
    make test
popd
%endif

#-----------------------------------------------------------------------
%install
install -d %{buildroot}/%{_prefix}
install -d %{buildroot}/%{_libdir}

make install -C objs prefix=%{buildroot}%{_prefix} libdir=%{buildroot}%{_libdir}
%if %{build_multiarch}
make install-libs -C objs32 prefix=%{buildroot}%{_prefix}
%endif

install -d %{buildroot}/%{_lib}
mv %{buildroot}%{_libdir}/*.so.* %{buildroot}/%{_lib}/
ln -s ../../%{_lib}/libz.so.%{version} %{buildroot}%{_libdir}/

%if %{build_multiarch}
install -d %{buildroot}/lib
mv %{buildroot}%{_prefix}/lib/*.so.* %{buildroot}/lib/
ln -s ../../lib/libz.so.%{version} %{buildroot}%{_prefix}/lib/
%endif

%if %{with dietlibc}
install -m644 objsdietlibc/libz.a -D %{buildroot}%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif

%if %{with uclibc}
#install -m644 objsuclibc/libz.a -D %{buildroot}%{uclibc_root}%{_libdir}/libz.a
make install-libs-only -C objsuclibc prefix=%{buildroot}%{uclibc_root} libdir=%{buildroot}%{uclibc_root}%{_libdir}
%endif
