from neuron import h
import numpy as np
import math
from scipy import signal
from excitationMechanismClass import *
from psutil import virtual_memory
import os

from nameSetters import *


class StimIntra(ExcitationMechanism):
    """
    stimType: INTRA or EXTRA cellular stimulation
    axon: axon object on which the stimulation is applied
    pos: position of the stimulus
    sect: section being stimulated
    delay: pulse delay (ms)
    stimDur: pulse duration (ms)
    amp: pulse amplitude (nA)
    freq: frequency of the sin pulse (Hz)
    duty_cycle: Percentage stimulus is ON for one period (t_ON = duty_cyle*1/f)
    stim_coord=[xe,ye,ze]: spatial coordinates  of the stimulating electrode
    waveform: Type of waveform either "MONOPHASIC" or "BIPHASIC" symmetric
    """
    def __init__(self, stimDur, amplitude, frequency, dutyCycle, waveform, timeRes, delay=0, invert=False):

        self.waveform = waveform

        self.stimDur = stimDur
        self.frequency = frequency
        self.amplitude = amplitude
        self.dutyCycle = dutyCycle
        self.delay = delay

        self.timeRes = timeRes

        self.t = np.arange(0, self.stimDur, timeRes)

        if self.waveform == 'MONOPHASIC':
            self.stimulusSignal = self.amplitude * 0.5 * signal.square(2 * np.pi * self.frequency * self.t, duty=dutyCycle) + self.amplitude * 0.5
        elif self.waveform == 'BIPHASIC':
            self.stimulusSignal = self.amplitude * signal.square(2 * np.pi * self.frequency * self.t, duty=dutyCycle)
        else:
            print "You didn't choose the right waveform either MONOPHASIC or BIPHASIC, it has been set to default MONOPHASIC"
            self.stimulusSignal = self.amplitude * 0.5 * signal.square(2 * np.pi * self.frequency * self.t, duty=dutyCycle) + self.amplitude * 0.5

        if invert:
            self.stimulusSignal = -self.stimulusSignal


        # add delay
        self.stimulusSignalDelayed = np.concatenate((np.zeros(self.delay/timeRes), self.stimulusSignal))

        # end with a zero, otherwise final value is valid for the rest of the simulation...
        self.stimulusSignalDelayed = np.concatenate((self.stimulusSignalDelayed, [0]))

        self.svec = h.Vector(self.stimulusSignalDelayed)

    def connect_axon(self, axon):

        # Place an IClamp on the first element of the allseclist
        # In unmyelinated axon case allseclist is directly the unique axon section

        stim = h.IClamp(0, axon.allseclist)
        stim.dur = self.stimDur + self.delay
        self.svec.play(stim._ref_amp, self.timeRes)

        excitationMechanismVars = [stim]
        axon.append_ex_mech_vars(excitationMechanismVars)

    def delete_neuron_objects(self):
        self.svec = None

class StimCuff(ExcitationMechanism):
    """
    stimType: INTRA or EXTRA cellular stimulation
    axon: axon object on which the stimulation is applied
    pos: position of the stimulus
    sect: section being stimulated
    delay: pulse delay (ms)
    stimDur: pulse duration (ms)
    amp: pulse amplitude (nA)
    freq: frequency of the sin pulse (Hz)
    duty_cycle: Percentage stimulus is ON for one period (t_ON = duty_cyle*1/f)
    stim_coord=[xe,ye,ze]: spatial coordinates  of the stimulating electrode
    waveform: Type of waveform either "MONOPHASIC" or "BIPHASIC" symmetric
    """
    def __init__(self, stimDur, amplitude, frequency, dutyCycle, radius, waveform, timeRes, delay=0, invert=False, rho=500):

        self.waveform = waveform

        numberContactPoints = 20 # more or less angle-independent field (<1% difference at 80% of the electrode radius)
        angles = 2*np.pi/numberContactPoints*np.arange(numberContactPoints)
        self.stim_coord = np.column_stack((np.zeros(numberContactPoints), radius*np.cos(angles), radius*np.sin(angles)))

        self.stimDur = stimDur
        self.frequency = frequency
        self.amplitude = amplitude/numberContactPoints
        self.dutyCycle = dutyCycle
        self.delay = delay
        self.radius = radius

        self.rho = rho

        self.timeRes = timeRes

        # # self.t = np.linspace(0, self.stimDur, (tStop+2*timeRes)/timeRes, endpoint=True)
        # self.t = np.arange(0, self.stimDur, timeRes)
        #
        # if self.waveform == 'MONOPHASIC':
        #     self.stimulusSignal = self.amplitude * 0.5 * signal.square(2 * np.pi * self.frequency * self.t, duty=dutyCycle) + self.amplitude * 0.5
        # elif self.waveform == 'BIPHASIC':
        #     self.stimulusSignal = self.amplitude * signal.square(2 * np.pi * self.frequency * self.t, duty=dutyCycle)
        # else:
        #     print "You didn't choose the right waveform either MONOPHASIC or BIPHASIC, it has been set to default MONOPHASIC"
        #     self.stimulusSignal = self.amplitude * 0.5 * signal.square(2 * np.pi * self.frequency * self.t, duty=dutyCycle) + self.amplitude * 0.5
        #
        # if invert:
        #     self.stimulusSignal = -self.stimulusSignal

        self.t, self.stimulusSignal = rectangularStimulusSignal(stimDur, amplitude, frequency, dutyCycle, waveform,
                                                                timeRes, delay, invert)


        # add delay
        self.stimulusSignalDelayed = np.concatenate((np.zeros(self.delay/timeRes), self.stimulusSignal))

        # end with a zero, otherwise final value is valid for the rest of the simulation...
        self.stimulusSignalDelayed = np.concatenate((self.stimulusSignalDelayed, [0]))

        self.svec = h.Vector(self.stimulusSignalDelayed)

    def connect_axon(self, axon):

        axon.setrx(self.stim_coord, axon.axonPosition, rho=self.rho)
        self.svec.play(h._ref_is_xtra, self.timeRes)

    def delete_neuron_objects(self):
        self.svec = None


class SimpleIClamp(ExcitationMechanism):

    def __init__(self, delay, stimDur, amplitude):

        self.delay = delay
        self.stimDur = stimDur
        self.amplitude = amplitude


    def connect_axon(self, axon):

        # Place an IClamp on the first element of the allseclist
        # In unmyelinated axon case allseclist is directly the unique axon section

        stim = h.IClamp(0, axon.allseclist)
        stim.delay = self.delay
        stim.dur = self.stimDur
        stim.amp = self.amplitude

        excitationMechanismVars = [stim]
        axon.append_ex_mech_vars(excitationMechanismVars)

    def delete_neuron_objects(self):
        pass

def rectangularStimulusSignal(stimDur, amplitude, frequency, dutyCycle, waveform, timeRes, delay=0, invert=False):

    t = np.arange(0, stimDur, timeRes)

    if waveform == 'MONOPHASIC':
        stimulusSignal = amplitude * 0.5 * signal.square(2 * np.pi * frequency * t, duty=dutyCycle) + amplitude * 0.5
    elif waveform == 'BIPHASIC':
        stimulusSignal = amplitude * signal.square(2 * np.pi * frequency * t, duty=dutyCycle)
    else:
        print "You didn't choose the right waveform either MONOPHASIC or BIPHASIC, it has been set to default MONOPHASIC"
        stimulusSignal = amplitude * 0.5 * signal.square(2 * np.pi * frequency * t, duty=dutyCycle) + amplitude * 0.5

    if invert:
        stimulusSignal = -stimulusSignal

    return t, stimulusSignal


class StimTripolarPoint(ExcitationMechanism):
    """
    axon: axon object on which the stimulation is applied
    pos: position of the stimulus
    sect: section being stimulated
    delay: pulse delay (ms)
    stimDur: pulse duration (ms)
    amp: pulse amplitude (nA)
    freq: frequency of the sin pulse (Hz)
    duty_cycle: Percentage stimulus is ON for one period (t_ON = duty_cyle*1/f)
    stim_coord=[xe,ye,ze]: spatial coordinates  of the stimulating electrode
    waveform: Type of waveform either "MONOPHASIC" or "BIPHASIC" symmetric
    """
    def __init__(self, radius, poleDistance, stimDur, amplitude, frequency, dutyCycle, waveform, timeRes, delay=0, invert=False, rho=500):

        self.waveform = waveform

        self.stim_coord = np.column_stack((np.array([0,1,2,1])*poleDistance, radius*np.ones(4), np.zeros(4)))

        self.stimDur = stimDur
        self.frequency = frequency
        self.amplitude = amplitude
        self.dutyCycle = dutyCycle
        self.delay = delay
        self.radius = radius

        self.rho = rho

        self.timeRes = timeRes

        self.t, self.stimulusSignal = rectangularStimulusSignal(stimDur, amplitude, frequency, dutyCycle, waveform,
                                                                timeRes, delay, invert)

        # add delay
        self.stimulusSignalDelayed = np.concatenate((np.zeros(self.delay/timeRes), self.stimulusSignal))

        # end with a zero, otherwise final value is valid for the rest of the simulation...
        self.stimulusSignalDelayed = np.concatenate((self.stimulusSignalDelayed, [0]))

        self.svec = h.Vector(self.stimulusSignalDelayed)

    def connect_axon(self, axon):

        axon.setrx(self.stim_coord, axon.axonPosition, bipolar = True, rho=self.rho)
        self.svec.play(h._ref_is_xtra, self.timeRes)


    def delete_neuron_objects(self):
        self.svec = None


class StimField(ExcitationMechanism):

    def __init__(self, fieldDirectory, stimTime, timeRes, bundle, origin=(0,0,0), interpolMethod='linear'):
        """
        StimField takes the location of a field saved as one 4D-matrix with the entries (x,y,z) and phi, the potentials.
        Multiple points in time are saved as multiple files that need to sort by name (DON'T just name them
        x1,...,x9,x10,... that will mix up to x1, x10, ..., x9. Use zero-padding.).

        The time step of the stimulation field is better to be chosed much higher than the one in the simulation.
        An interpolation will be done internally. Sampling rates too high cause delays due to loading, saving, etc.

        StimField is intended for use with FEM-simulations.

        Args:
            fieldDirectory: directory the field files are in (and only the field files)
            stimTime: duration of the stimulation
            timeRes: sampling rate of the stimulation
            bundle: bundle object (needed for axon geometries
            origin: point where the field's (0,0,0) will be put in the bundle-space
            interpolMethod: interpolation between points of the input field.
        """


        # get file names
        filenames = [f for f in sorted(os.listdir(fieldDirectory)) if os.path.isfile(os.path.join(fieldDirectory, f))]

        # load example field to check dimensions
        field = np.loadtxt(os.path.join(fieldDirectory, filenames[0]))

        # # irregular grid or regular?
        # irregular = False
        # for i in range(3):
        #     coordData = field[i,:]
        #     stepSizes = np.unique(np.diff(np.sort(coordData)))
        #     if len(stepSizes) > 2:
        #         irregular = True
        #         break
        # if irregular:
        #     print 'The voltage field data is not on a regular grid. No linear interpolation will be done. ' \
        #           'Consider using a regular grid.'

        # check the dimensions of input field and number of points that need to be interpolated
        numInterPointsAll, nsegAxonwise = bundle.approx_num_segs()
        expectedSizeAllAxons = numInterPointsAll*stimTime/timeRes*8
        memorySize = virtual_memory().total

        # memory considerations
        if field.nbytes > 0.5*memorySize:
            raise Exception('Too many field points.')
        elif expectedSizeAllAxons+field.nbytes > 0.7*memorySize:
            print 'Interpolation of field points needs to be done several times because of memory shortage.'


        # aproximated memory consumption of axon stimulation signals
        memoryUsageAxonwise = np.array(nsegAxonwise)*stimTime/timeRes*8

        # make a list of axons to go through in this run
        # first check memory


        freeMemory = virtual_memory().free
        memLimit = freeMemory * 0.8

        memLimit = 600000

        if expectedSizeAllAxons < memLimit:
            currentAxonIndices = range(len(bundle.axons))
            remainingAxonIndices = range(len(bundle.axons))
        else:
            cumSizeAxons = np.cumsum(memoryUsageAxonwise)
            lastIndex = np.searchsorted(cumSizeAxons, memLimit)
            if lastIndex == 0:
                raise Exception('Not enough memory.')
            currentAxonIndices = range(lastIndex)
            remainingAxonIndices = range(lastIndex, len(bundle.axons))

        while not remainingAxonIndices == []:

            # array to save the potentials for each segment of the current axons for each time step
            segmentPotentials = [[[] for j in range(len(filenames))] for i in range(len(currentAxonIndices))]

            timeIndex = 0
            for filename in filenames:

                # load example field to check dimensions
                fieldNoOffset = np.loadtxt(os.path.join(fieldDirectory, filename))

                fieldCoordsNoOffset = fieldNoOffset[0:3,:]
                fieldValues = fieldNoOffset[3,:]

                # apply anchor point
                fieldCoords = np.transpose(fieldCoordsNoOffset) - np.tile(origin, (fieldCoordsNoOffset.shape[1], 1))

                # configure the interpolator
                if interpolMethod == 'nearest':
                    from scipy.interpolate import NearestNDInterpolator
                    interpolator = NearestNDInterpolator(fieldCoords, fieldValues)
                elif interpolMethod == 'linear':
                    from scipy.interpolate import LinearNDInterpolator
                    interpolator = LinearNDInterpolator(fieldCoords, fieldValues)
                # elif interpolMethod == 'rbf':
                #     if field.shape[0] < 7000:
                #         from scipy.interpolate import Rbf
                #         self.interpolator = Rbf(self.field[:,0], self.field[:,1], self.field[:,2], self.field[:,3])  # radial basis function interpolator instance
                #     else:
                #         raise Exception('Too many field points for radial basis function interpolation. Max 7000.')
                else:
                    raise NameError('Chosen interpolation method not valid. Choose from "nearest", "linear" and "rbf".')

                # interpolate the potentials for segments todo
                for axonIndex in currentAxonIndices:

                    # get axon
                    axon = bundle.axons[axonIndex]

                    # create neuron object to obtain the segment middle points
                    axon.create_neuron_object()

                    # get segment middle points
                    x, y, z = axon.xmid, axon.ymid, axon.zmid

                    # interpolate
                    potentials = interpolator(x, y, z)

                    # save in big matrix (#current axons x #time steps x #segments (axon-dependent)
                    segmentPotentials[axonIndex-currentAxonIndices[0]][timeIndex] = potentials

                    # delete neuron object!
                    axon.delete_neuron_object()

                timeIndex += 1

            # save data to disk. One axon gets one file as they are loaded axonwise later on.
            for localIndex in range(len(currentAxonIndices)):
                # actualAxonIndex = localIndex + currentAxonIndices[0]

                # get the potential for one axon (all segments, all timesteps)
                potentials = segmentPotentials[localIndex]

                # TODO: adjust sampling rate in memory-efficient way

                # save in the same manner as recordings
                saveFilename = get_file_name('', bundle.basePath)

                # save the potentals to disk
                np.savetxt(saveFilename, potentials)


            # delete worked axons from list
            for removeAxonIndex in currentAxonIndices:
                if removeAxonIndex in remainingAxonIndices:
                    remainingAxonIndices.remove(removeAxonIndex)

            # create new current list
            firstIndex = remainingAxonIndices[0]
            cumSizeAxons = np.cumsum(memoryUsageAxonwise[remainingAxonIndices])
            lastIndex = np.searchsorted(cumSizeAxons, memLimit) + firstIndex
            currentAxonIndices = range(firstIndex, lastIndex)



    def connect_axon(self, axon):
        print 'Not implemented.'

    def delete_neuron_objects(self):
        print 'Not implemented.'