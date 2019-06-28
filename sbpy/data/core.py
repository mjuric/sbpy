# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
================
sbpy Data Module
================

created on June 22, 2017
"""

from copy import deepcopy
from collections import OrderedDict
from numpy import ndarray, array
from astropy.table import QTable, Column, vstack
import astropy.units as u

from . import conf
from .. import exceptions

__all__ = ['DataClass', 'DataClassError']


class DataClassError(exceptions.SbpyException):
    pass


class DataClass():
    """`~sbpy.data.DataClass` serves as the base class for all data
    container classes in `sbpy` in order to provide consistent
    functionality. Classes derived from `~sbpy.data.DataClass` have
    the following properties:

    The core of `~sbpy.data.DataClass` is an `~astropy.table.QTable`
    object (referred to as the `data table` below) - a type of
    `~astropy.table.Table` object that supports the `~astropy.units`
    formalism on a per-column base - which already provides most of
    the required functionality. `~sbpy.data.DataClass` objects can be
    manually generated from dictionaries
    (`~sbpy.data.DataClass.from_dict`), list-like objects on a
    per-column basis (`~sbpy.data.DataClass.from_columns`) or a
    per-row basis (`~sbpy.data.DataClass.from_rows`), or directly from
    another `~astropy.table.QTable` object. It is possible to write
    `~sbpy.data.DataClass` objects to a file and from a file.

    `~sbpy.data.DataClass` objects can hold meta data that are stored
    as `~astropy.table.QTable` meta data and can be accessed as a
    `~sbpy.data.DataClass` property. Furthermore,
    `~sbpy.data.DataClass` objects have the ability to recognize
    alternative names for properties stored in the data table and even
    do transformations.

    A few high-level functions for table data access or modification
    are provided; other, more complex modifications can be applied to
    the underlying table object (`~sbpy.data.DataClass.table`) directly.
    """

    def __init__(self):
        self._table = QTable()

    @staticmethod
    def _unit_apply(val, unit):
        """Convenience function that applies a unit to a value, or converts
        a `~astropy.units.Quantity` to this units if possible.

        Parameters
        ----------
        val : `~astropy.units.Quantity` or unit-less type
            Input value.
        unit : str or None
            Unit into which ``val`` will be converted. If None, ``val`` is
            considered not to be a `~astropy.units.Quantity`.

        Returns
        -------
        `~astropy.units.Quantity` or other

        """
        if unit is None:
            return val
        elif isinstance(val, u.Quantity):
            return val.to(unit)
        else:
            return val * u.Unit(unit)

    @staticmethod
    def _unit_convert_strip(val, unit):
        """Convenience function that transforms `~astropy.units.Quantities`
        and then strips the unit, but leaves non-Quantities untouched.

        Parameters
        ----------
        val : `~astropy.units.Quantity` or unit-less type
            Input value.
        unit : str or None
            Unit into which ``val`` will be converted. If None, ``val`` is
            considered not to be a `~astropy.units.Quantity`.

        Returns
        -------
        unit-less type
        """
        if unit is None:
            return val
        else:
            return DataClass._unit_apply(val, unit).value

    @classmethod
    def from_dict(cls, data, meta={}, **kwargs):
        """Create `~sbpy.data.DataClass` object from dictionary.

        Parameters
        ----------
        data : `~collections.OrderedDict` or dictionary
            Data that will be ingested in `~sbpy.data.DataClass`
            object. Each item in the dictionary will form a column in
            the data table. The item key will be used as column name,
            the item value, which must be a list-like
            `~astropy.units.Quantity`, will be used as data. All
            columns, i.e., all item values, must have the same length.
        meta : dictionary, optional
            Meta data that will be stored in the data table. Default:
            empty dictionary
        kwargs : additional keyword arguments, optional
            Additional keyword arguments that will be passed on to
            `~astropy.table.QTable` in the creation of the underlying
            data table.

        Returns
        -------
        `DataClass` object

        Examples
        --------
        The following example creates a single-row `~sbpy.data.Orbit`
        object.

        >>> import astropy.units as u
        >>> from sbpy.data import Orbit
        >>> orb = Orbit.from_dict({'a': [2.7674]*u.au,
        ...                        'e': [0.0756],
        ...                        'i': [10.59321]*u.deg})

        Since dictionaries have no specific order, the ordering of the
        column in the example above is not defined. If your data table
        requires a specific order, use ``OrderedDict``:

        >>> from collections import OrderedDict
        >>> orb = Orbit.from_dict(OrderedDict([('a', [2.7674, 3.123]*u.au),
        ...                                    ('e', [0.0756, 0.021]),
        ...                                    ('i', [10.59, 3.21]*u.deg)]))
        >>> print(orb)
        <QTable length=2>
           a       e       i
           AU             deg
        float64 float64 float64
        ------- ------- -------
         2.7674  0.0756   10.59
          3.123   0.021    3.21
        """
        self = cls()
        self._table = QTable(data, meta=meta, **kwargs)
        return self

    @classmethod
    def from_columns(cls, columns, names, units=None, meta={}, **kwargs):
        """Create `~sbpy.data.DataClass` object from a sequence. If that
        sequence is one-dimensional, it is interpreted as
        a single column; if it is two-dimensional, it is interpreted as a
        sequence of columns.

        Parameters
        ----------
        columns : list, `~numpy.ndarray`, tuple, or `~astropy.units.Quantity`
            Data that will be ingested in `DataClass` object. A
            one-dimensional sequence is interpreted as a single column.
            A two-dimensional sequence is interpreted as a sequence of
            columns, each of which must have the same length.
        names : str or list-like
            Column names, must have the same number of names as data columns.
        units : str or list-like, optional
            Unit labels (as provided by `~astropy.units.Unit`) in which
            the data provided in ``columns`` will be stored in the underlying
            table. If None is provided, the units as provided by ``columns``
            are used. Default: None
        meta : dictionary, optional
            Meta data that will be stored in the data table. Default:
            empty dictionary
        kwargs : additional keyword arguments, optional
            Additional keyword arguments that will be passed on to
            `~astropy.table.QTable` in the creation of the underlying
            data table.

        Returns
        -------
        `DataClass` object

        Examples
        --------
        The following example creates a single-column `~sbpy.data.Ephem`
        object.

        >>> from sbpy.data import Ephem
        >>> import astropy.units as u
        >>> eph = Ephem.from_columns([1, 2, 3, 4]*u.au,
        ...                          names='a')
        >>> eph
        <QTable length=4>
           a
           AU
        float64
        -------
            1.0
            2.0
            3.0
            4.0

        This example creates a two-column `~sbpy.data.Ephem` object in which
        units are assigned using the optional ``units`` keyword argument.

        >>> eph = Ephem.from_columns([[1, 2, 3, 4],
        ...                               [90, 50, 30, 10]],
        ...                              names=['r', 'alpha'],
        ...                              units=['au', 'deg'])
        >>> eph
        <QTable length=4>
           r     alpha
           AU     deg
        float64 float64
        ------- -------
            1.0    90.0
            2.0    50.0
            3.0    30.0
            4.0    10.0

        If units are provided in ``columns`` and ``units``, those units in
        ``columns`` will be transformed into those in ``units`` on a
        per-column basis.

        >>> eph = Ephem.from_columns([[1, 2, 3, 4]*u.au,
        ...                           [90, 50, 30, 10]*u.deg],
        ...                           names=['r', 'alpha'],
        ...                           units=['km', 'rad'])
        >>> eph
        <QTable length=4>
                r                 alpha
                km                 rad
             float64             float64
        ------------------ -------------------
               149597870.7  1.5707963267948966
               299195741.4  0.8726646259971648
        448793612.09999996  0.5235987755982988
               598391482.8 0.17453292519943295
        """

        if isinstance(columns, (list, ndarray, tuple, u.Quantity)):
            # reorganize columns, if necessary
            try:
                array(columns).shape[1]
            except IndexError:
                columns = [columns]
            # reorganize names, if necessary
            if isinstance(names, str):
                names = [names]
        else:
            raise DataClassError('columns must be a list, tuple, '
                                 'numpy array, or a Quantity')

        if units is not None:
            if all([isinstance(col, u.Quantity) for col in columns]):
                # if columns has units, transform to `units`
                columns = [val.to(unit) for val, unit in
                           list(zip(columns, units))]
            else:
                # if columns has no units, apply `units`
                columns = [val*u.Unit(unit) if unit is not None else val
                           for val, unit in
                           list(zip(columns, units))]

        self = cls()
        self._table = QTable(columns, names=names, meta=meta, **kwargs)
        return self

    @classmethod
    def from_rows(cls, rows, names, units=None, meta={}, **kwargs):
        """Create `~sbpy.data.DataClass` object from a sequence. If that
        sequence is one-dimensional, it is interpreted as
        a single row; if it is two-dimensional, it is interpreted as a
        sequence of rows.

        Parameters
        ----------
        rows : list, `~numpy.ndarray`, or tuple
            Data that will be ingested in `DataClass` object. A
            one-dimensional sequence is interpreted as a single row.
            A two-dimensional sequence is interpreted as a sequence of
            rows, each of which must have the same length.
        names : str or list
            Column names, must have the same number of names as data columns
            in each row.
        units : str or list-like, optional
            Unit labels (as provided by `~astropy.units.Unit`) in which
            the data provided in ``rows`` will be stored in the underlying
            table. If None is provided, the units as provided by ``rows``
            are used. Default: None
        meta : dictionary, optional
            Meta data that will be stored in the data table. Default:
            empty dictionary
        kwargs : additional keyword arguments, optional
            Additional keyword arguments that will be passed on to
            `~astropy.table.QTable` in the creation of the underlying
            data table.

        Returns
        -------
        `DataClass` object

        Examples
        --------
        The following example creates a single-row `~sbpy.data.Phys` object.

        >>> from sbpy.data import Phys
        >>> import astropy.units as u
        >>> phys = Phys.from_rows([1*u.km, 0.05, 17*u.mag],
        ...                       names=['diam', 'pv', 'absmag'])
        >>> phys
        <QTable length=1>
          diam     pv    absmag
           km             mag
        float64 float64 float64
        ------- ------- -------
            1.0    0.05    17.0

        Providing ``units`` allows providing unit-less data in ``rows``:

        >>> phys = Phys.from_rows([[1, 0.05, 17],
        ...                        [2, 0.05, 16]],
        ...                       names=['diam', 'pv', 'absmag'],
        ...                       units=['km', None, 'mag'])
        >>> phys
        <QTable length=2>
          diam     pv    absmag
           km             mag
        float64 float64 float64
        ------- ------- -------
            1.0    0.05    17.0
            2.0    0.05    16.0
        """

        if isinstance(names, str):
            names = [names]
        if isinstance(units, (str, u.Unit)):
            units = [units]
        if units is not None and len(names) != len(units):
            raise DataClassError('Must provide the same number of names '
                                 'and units.')

        if units is None:
            # get units used in `rows`
            # first check whether `rows` is a single row or multiple rows
            try:
                iter(rows[0])
            except TypeError:
                # convert rows to list of list
                rows = [rows]

            # extract units
            units = []
            for col in rows[0]:
                if isinstance(col, u.Quantity):
                    units.append(col.unit)
                else:
                    units.append(None)

        # build unit-less array of columns from rows
        columns = array([[cls._unit_convert_strip(vj, units[j])
                          for j, vj in enumerate(vi)]
                         for vi in rows]).transpose()

        return cls.from_columns(columns=columns,
                                units=units,
                                names=names,
                                meta=meta,
                                **kwargs)

    @classmethod
    def from_table(cls, table, meta={}, **kwargs):
        """Create `DataClass` object from `~astropy.table.Table` or
        `astropy.table.QTable` object.

        Parameters
        ----------
        table : astropy `Table` object, mandatory
             Data that will be ingested in `DataClass` object.
        meta : dictionary, optional
            Meta data that will be stored in the data table. If ``table``
            already holds meta data, ``meta`` will be added. Default:
            empty dictionary
        kwargs : additional keyword arguments, optional
            Additional keyword arguments that will be passed on to
            `~astropy.table.QTable` in the creation of the underlying
            data table.

        Returns
        -------
        `DataClass` object

        Examples
        --------
        >>> from astropy.table import QTable
        >>> import astropy.units as u
        >>> from sbpy.data import DataClass
        >>> tab = QTable([[1,2,3]*u.kg,
        ...               [4,5,6]*u.m/u.s,],
        ...              names=['mass', 'velocity'])
        >>> dat = DataClass.from_table(tab)
        >>> print(dat.table)
        mass velocity
         kg   m / s
        ---- --------
         1.0      4.0
         2.0      5.0
         3.0      6.0
        """

        self = cls()
        self._table = QTable(table, meta={**table.meta, **meta}, **kwargs)

    @classmethod
    def from_file(cls, filename, meta={}, **kwargs):
        """Create `DataClass` object from a file using
        `~astropy.table.Table.read`.

        Parameters
        ----------
        filename : str
             Name of the file that will be read and parsed.
        meta : dictionary, optional
             Meta data that will be stored in the data table. If the data
             to be read
             already holds meta data, ``meta`` will be added. Default:
             empty dictionary
        kwargs : additional parameters
             Optional parameters that will be passed on to
             `~astropy.table.Table.read`.

        Returns
        -------
        `DataClass` object

        Notes
        -----
        This function is merely a wrapper around
        `~astropy.table.Table.read`. Please refer to the documentation of
        that function for additional information on optional parameters
        and data formats that are available. Furthermore, note that this
        function is not able to identify units. If you want to work with
        `~astropy.units` you have to assign them manually to the object
        columns.

        Examples
        --------
        >>> from sbpy.data import DataClass

        >>> dat = DataClass.from_file('data.txt',
        ...                           format='ascii') # doctest: +SKIP
        """

        data = QTable.read(filename, **kwargs)

        self = cls()
        self._table = data
        self._table.meta = {**self._table.meta, **meta}

        return self

    def to_file(self, filename, format='ascii', **kwargs):
        """Write object to a file using
        `~astropy.table.Table.write`.

        Parameters
        ----------
        filename : str
             Name of the file that will be written.
        format : str, optional
             Data format in which the file should be written. Default:
             ``ASCII``
        kwargs : additional parameters
             Optional parameters that will be passed on to
             `~astropy.table.Table.write`.

        Returns
        -------
        None

        Notes
        -----
        This function is merely a wrapper around
        `~astropy.table.Table.write`. Please refer to the
        documentation of that function for additional information on
        optional parameters and data formats that are
        available. Furthermore, note that this function is not able to
        write unit information to the file.

        Examples
        --------
        >>> from sbpy.data import DataClass
        >>> import astropy.units as u
        >>> dat = DataClass.from_array([[1, 2, 3]*u.deg,
        ...                             [4, 5, 6]*u.km,
        ...                             ['a', 'b', 'c']],
        ...                            names=('a', 'b', 'c'))
        >>> dat.to_file('test.txt')

        """

        self._table.write(filename, format=format, **kwargs)

    def __len__(self):
        """Get number of data elements in _table"""
        return len(self._table)

    def __getattr__(self, field):
        """Get attribute from ``self._table` (columns, rows); checks
        for and may use alternative field names."""

        if field in dir(self):
            return self.field
        else:
            try:
                field = self._translate_columns(field)[0]
                return self._table[field]
            except (KeyError, IndexError, AttributeError):
                raise AttributeError('Attribute {:s} not available.'.format(
                    field))

    def __repr__(self):
        """Return representation of the underlying data table
        (``self._table.__repr__()``)"""
        return self._table.__repr__()

    def __getitem__(self, ident):
        """Return columns or rows from data table(``self._table``); checks
        for and may use alternative field names."""

        # iterable
        if isinstance(ident, (list, tuple, ndarray)):
            if all([isinstance(i, str) for i in ident]):
                # list of column names
                self = self._convert_columns(ident)
                newkeylist = [self._translate_columns(i)[0] for i in ident]
                ident = newkeylist
                # return as new DataClass object
                return self.from_table(self._table[ident])
            # ignore lists of boolean (masks)
            elif all([isinstance(i, bool) for i in ident]):
                pass
            # ignore lists of integers
            elif all([isinstance(i, int) for i in ident]):
                pass
        # individual strings
        elif isinstance(ident, str):
            self = self._convert_columns(ident)
            ident = self._translate_columns(ident)[0]
        elif isinstance(ident, int):
            return self.from_table(self._table[ident])

        # return as element from self_table
        return self._table[ident]

    def __setitem__(self, *args):
        """Refer cls.__setitem__ to self._table"""
        self._table.__setitem__(*args)

    def _translate_columns(self, target_colnames):
        """Translate target_colnames to the corresponding column names
        present in this object's table. Returns a list of actual column
        names present in this object that corresponds to target_colnames
        (order is preserved). Raises KeyError if not all columns are
        present or one or more columns could not be translated.
        """

        if not isinstance(target_colnames, (list, ndarray, tuple)):
            target_colnames = [target_colnames]

        translated_colnames = deepcopy(target_colnames)
        for idx, colname in enumerate(target_colnames):
            # colname is already a column name in self.table
            if colname in self.column_names:
                continue
            # colname is an alternative column name
            elif colname in sum(conf.fieldnames, []):
                for alt in conf.fieldnames[conf.fieldname_idx[colname]]:
                    # translation available for colname
                    if alt in self.column_names:
                        translated_colnames[idx] = alt
                        break
            # colname is unknown, raise a KeyError
            else:
                raise KeyError('field {:s} not available.'.format(
                    colname))

        return translated_colnames

    def _convert_columns(self, target_colnames):
        """Convert target_colnames, if necessary. Converted columns will be
        added as columns to ``self`` using the field names provided in
        target_colnames. No error is returned by this function if a
        field could not be converted.
        """

        if not isinstance(target_colnames, (list, ndarray, tuple)):
            target_colnames = [target_colnames]

        for colname in target_colnames:
            # ignore, if colname is unknown (KeyError)
            try:
                # ignore if colname has already been converted
                if any([alt in self.column_names for alt
                        in conf.fieldnames[conf.fieldname_idx[colname]]]):
                    continue
                # consider alternative names for colname -> alt
                for alt in conf.fieldnames[conf.fieldname_idx[colname]]:
                    if alt in list(conf.field_eq.keys()):
                        # conversion identified
                        convname = self._translate_columns(
                            list(conf.field_eq[alt].keys())[0])[0]
                        convfunc = list(conf.field_eq[alt].values())[0]
                        if convname in self.column_names:
                            # create new column for the converted field
                            self.add_column(convfunc(self.table[convname]),
                                            colname)
                            break
            except KeyError:
                continue

        return self

    @property
    def table(self):
        """Return `~astropy.table.QTable` object containing all data."""
        return self._table

    @property
    def column_names(self):
        """Return a list of all column names in the data table."""
        return self._table.columns

    @property
    def meta(self):
        """Enables access to the ``meta`` data of the underlying data table.

        Examples
        --------
        >> > from sbpy.data import DataClass
        >> > import astropy.units as u
        >> > data = DataClass.from_columns([[1, 2, 3, 4]*u.kg,
        ...                                [5, 6, 7, 8]*u.m],
        ...                               names=['a', 'b'],
        ...                               meta={'origin': 'measured'})
        >> > data.meta  # meta data access
        {'origin': 'measured'}
        >> > data.meta['date'] = '2019-06-27'  # meta data modification
        >> > data.meta['date']
        '2019-06-27'
        """
        return self._table.meta

    def add_rows(self, rows, join_type='inner'):
        """Append additional rows to the existing data table. An individual
        row can be provided in list, tuple, `~numpy.ndarray`, or
        dictionary form. Multiple rows can be provided in the form of
        a list, tuple, or `~numpy.ndarray` of individual
        rows. Multiple rows can also be provided in the form of a
        `~astropy.table.QTable` or another `~sbpy.data.DataClass`
        object. Parameter ``join_type`` defines which columns appear
        in the final output table: ``inner`` only keeps those columns
        that appear in both the original table and the rows to be
        added; ``outer`` will keep all columns and populate some with
        placeholders, if necessary. In case of a list, the list
        elements must be in the same order as the table columns. In
        either case, matching `~astropy.units` must be provided in
        ``rows`` if used in the data table.

        Parameters
        ----------
        rows: list, tuple, `~numpy.ndarray`, dict, or `~collections.OrderedDict`
            Data to be appended to the table; required to have the same
            length as the existing table, as well as the same units.
        join_type: str, optional
            Defines which columns are kept in the output table: ``inner``
            only keeps those columns that appear in both the original
            table and the rows to be added; ``outer`` will keep all
            columns and populate them with placeholders, if necessary.
            Default: ``inner``

        Returns
        -------
        n: int, the total number of rows in the data table

        Examples
        --------
        >> > from sbpy.data import DataClass
        >> > import astropy.units as u
        >> > dat = DataClass.from_array([[1, 2, 3]*u.Unit('m'),
        ...                             [4, 5, 6]*u.m/u.s,
        ...                             ['a', 'b', 'c']],
        ...                            names=('a', 'b', 'c'))
        >> > dat.add_rows({'a': 5*u.m, 'b': 8*u.m/u.s, 'c': 'e'})
        4
        >> > print(dat.table)
         a    b    c
         m  m / s
        --- ----- ---
        1.0   4.0   a
        2.0   5.0   b
        3.0   6.0   c
        5.0   8.0   e
        >> > dat.add_rows(([6*u.m, 9*u.m/u.s, 'f'],
        ...               [7*u.m, 10*u.m/u.s, 'g']))
        6
        >> > dat.add_rows(dat)
        12

        """
        if isinstance(rows, QTable):
            self._table = vstack([self._table, rows], join_type=join_type)
        if isinstance(rows, DataClass):
            self._table = vstack([self._table, rows.table],
                                 join_type=join_type)
        if isinstance(rows, (dict, OrderedDict)):
            try:
                newrow = [rows[colname] for colname in self._table.columns]
            except KeyError as e:
                raise ValueError('data for column {0} missing in row {1}'.
                                 format(e, rows))
            self.add_rows(newrow)
        if isinstance(rows, (list, ndarray, tuple)):
            if (not isinstance(rows[0], (u.quantity.Quantity, float)) and
                    isinstance(rows[0], (dict, OrderedDict,
                                         list, ndarray, tuple))):
                for subrow in rows:
                    self.add_rows(subrow)
            else:
                self._table.add_row(rows)
        return len(self._table)

    def add_column(self, data, name, **kwargs):
        """Append a single column to the current data table. The lenght of
        the input list, `~numpy.ndarray`, or tuple must match the current
        number of rows in the data table.

        Parameters
        ----------
        data: list, `~numpy.ndarray`, or tuple
            Data to be filled into the table; required to have the same
            length as the existing table's number rows.
        name: str
            Name of the new column; must be different from already existing
            column names.
        **kwargs: additional parameters
            Additional optional parameters will be passed on to
            `~astropy.table.Table.add_column`.

        Returns
        -------
        n: int, the total number of columns in the data table

        Examples
        --------
        >> > from sbpy.data import DataClass
        >> > import astropy.units as u
        >> > dat = DataClass.from_array([[1, 2, 3]*u.Unit('m'),
        ...                             [4, 5, 6]*u.m/u.s,
        ...                             ['a', 'b', 'c']],
        ...                            names=('a', 'b', 'c'))
        >> > dat.add_column([10, 20, 30]*u.kg, name='d')
        4
        >> > print(dat.table)
         a    b    c   d
         m  m / s      kg
        --- ----- --- ----
        1.0   4.0   a 10.0
        2.0   5.0   b 20.0
        3.0   6.0   c 30.0
        """

        self._table.add_column(Column(data, name=name), **kwargs)
        return len(self.column_names)
